from fastapi import FastAPI, HTTPException, Query
from youtube_comment_downloader import YoutubeCommentDownloader
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import os
import datetime
import yt_dlp

app = FastAPI(title="Whats Trending On Social Media", description="FastAPI server for fetching trending data from YouTube, TikTok, and Instagram Reels")

# Environment variable for TikTok API key
tiktok_key = os.getenv("tiktok")
if tiktok_key:
    os.environ["tiktok"] = tiktok_key

def _yt_trending(region: Optional[str] = None, limit: int = 10) -> List[Dict[str, str]]:
    url = "https://www.youtube.com/feed/trending"
    if region: url += f"?gl={region.upper()}"
    opts = {'extract_flat': True, 'force_generic_extractor': True, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return [{"title": v.get("title", "No Title"), "url": f"https://www.youtube.com/watch?v={v.get('id')}"} for v in info.get("entries", [])[:limit] if v.get("id")]
    except: return []

@app.get("/youtube/comments/{video_id}")
async def get_comments_yt(video_id: str, max_comments: int = Query(100, description="Maximum number of comments to fetch")) -> List[str]:
    """Fetch YouTube comments by video ID.
    Returns up to `max_comments` comment texts."""
    d = YoutubeCommentDownloader()
    comments = []
    try:
        for c in d.get_comments_from_url(f"https://www.youtube.com/watch?v={video_id}"):
            comments.append(c["text"])
            if len(comments) >= max_comments:
                break
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching comments: {str(e)}")
    return comments

@app.get("/youtube/trending/global")
async def get_yt_trending_global(limit: int = Query(10, description="Number of trending videos to fetch")) -> List[Dict[str, str]]:
    """Get trending YouTube videos globally (US).
    Returns list of titles and URLs."""
    return _yt_trending(limit=limit)

@app.get("/youtube/trending/{region_code}")
async def get_yt_trending_by_region(region_code: str = "AE", limit: int = Query(10, description="Number of trending videos to fetch")) -> List[Dict[str, str]]:
    """Get trending YouTube videos by region code.
    Returns list of titles and URLs."""
    return _yt_trending(region=region_code, limit=limit)

@app.get("/youtube/video-info")
async def get_yt_video_info(url: str = Query(..., description="YouTube video URL")) -> Optional[Dict[str, str]]:
    """Get metadata of a YouTube video from its URL.
    Includes title, views, likes, description, etc."""
    opts = {'quiet': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            i = ydl.extract_info(url, download=False)
            return {
                "title": i.get("title", ""),
                "channel": i.get("uploader", ""),
                "description": i.get("description", ""),
                "views": f"{i.get('view_count', 0):,}",
                "likes": f"{i.get('like_count', 0):,}" if i.get('like_count') else "N/A",
                "upload_date": i.get("upload_date", ""),
                "duration": f"{i.get('duration', 0)} seconds",
                "thumbnail": i.get("thumbnail", ""),
                "url": i.get("webpage_url", url),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching video info: {str(e)}")

@app.get("/tiktok/trending")
async def tiktok_trending_global() -> str:
    """Fetches and summarizes trending TikTok videos with stats and hashtags."""
    import os, requests, json
    h = {
        "x-rapidapi-key": os.getenv("tiktok"),
        "x-rapidapi-host": "tiktok-best-experience.p.rapidapi.com"
    }
    try:
        data = requests.get("https://tiktok-best-experience.p.rapidapi.com/trending", headers=h).json()
        if data.get("status") != "ok" or "data" not in data:
            raise HTTPException(status_code=500, detail="Invalid or failed response from TikTok API.")

        videos = data["data"].get("list", [])
        if not videos:
            return "⚠️ No trending videos found."

        summary = [f"✅ Found {len(videos)} trending TikTok videos.\n"]
        for i, video in enumerate(videos):
            hashtags = {
                tag["cha_name"]
                for tag in video.get("cha_list", [])
                if tag.get("cha_name")
            }
            hashtags.update({
                tag["hashtag_name"]
                for tag in video.get("text_extra", [])
                if tag.get("type") == 1 and tag.get("hashtag_name")
            })

            stats = video.get("statistics", {})
            plays = stats.get("play_count", 0)
            likes = stats.get("digg_count", 0)
            comments = stats.get("comment_count", 0)
            shares = stats.get("share_count", 0)
            saves = stats.get("collect_count", 0)
            engagement = ((likes + comments + shares) / plays) * 100 if plays > 0 else 0.0

            summary.append(f"""--- Video {i} ---
            Title: {video.get("author", {}).get("nickname", "N/A")}
            Description: {video.get("desc", "No description")}
            Link: {video.get("share_url", "No link")}
            Hashtags: {', '.join(hashtags)}
            📊 Metrics:
            - Plays: {plays:,}
            - Likes: {likes:,}
            - Comments: {comments:,}
            - Shares: {shares:,}
            - Saves: {saves:,}
            - Engagement Rate: {engagement:.2f}%
            {"=" * 40}
            """)

        return "\n".join(summary)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/instagram/reels/trends")
async def get_this_weeks_reels_trends() -> List[Dict[str, str]]:
    """Scrape this week's Instagram Reels trends.
    Returns list with trend name, date, and stats."""
    try:
        r = requests.get("https://later.com/blog/instagram-reels-trends/", headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch Instagram trends.")
        soup = BeautifulSoup(r.text, "html.parser")
        today = datetime.date.today()
        trends = []
        for h in soup.select("h3"):
            t = h.get_text(strip=True)
            if t.startswith("Trend:"):
                try:
                    name, date_str = t[len("Trend:"):].split("—")
                    trend_date = datetime.datetime.strptime(date_str.strip(), "%B %d, %Y").date()
                    if (today - trend_date).days > 30: continue
                    ps = h.find_next_siblings("p", limit=2)
                    trends.append({
                        "date": str(trend_date),
                        "trend": name.strip(),
                        "description": ps[0].get_text(strip=True) if ps else "",
                        "posts_info": ps[1].get_text(strip=True) if len(ps) > 1 else ""
                    })
                except: continue
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Instagram trends: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)