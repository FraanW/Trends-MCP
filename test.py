from youtube_comment_downloader import YoutubeCommentDownloader
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import json
import os
import datetime
from mcp.server.fastmcp import FastMCP
import yt_dlp

mcp = FastMCP(name="Trends-MCP",dependencies=["beautifulsoup4", "youtube-comment-downloader", "yt_dlp"])
os.environ["tiktok"]="f7c6c51065msh4ef412f8594dcb2p1591f7jsn272f54a72e4d"

@mcp.tool()
def get_comments_yt(video_id: str, max_comments: int = 100) -> List[str]:
    """Fetches up to `max_comments` comments from a given YouTube video ID."""
    downloader = YoutubeCommentDownloader()
    comments = []
    for comment in downloader.get_comments_from_url(f"https://www.youtube.com/watch?v={video_id}"):
        comments.append(comment["text"])
        if len(comments) >= max_comments:
            break
    return comments

@mcp.tool()
def get_yt_trending_global(limit: int = 10) -> List[Dict[str, str]]:
    """
    Uses yt-dlp to fetch trending YouTube videos from the global (US) region.

    Args:
        limit (int): Number of top videos to return.

    Returns:
        List[Dict[str, str]]: List of video titles and URLs.
    """
    ydl_opts = {
        'extract_flat': True,
        'force_generic_extractor': True,
        'quiet': True
    }

    trending_url = "https://www.youtube.com/feed/trending"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(trending_url, download=False)
            entries = info.get('entries', [])[:limit]

            return [
                {
                    "title": video.get("title", "No Title"),
                    "url": f"https://www.youtube.com/watch?v={video.get('id')}"
                }
                for video in entries
                if video.get("id")
            ]

        except Exception as e:
            print(f"❌ yt-dlp error: {e}")
            return []


@mcp.tool()
def get_yt_trending_by_region(region_code: str = "IN", limit: int = 10) -> List[Dict[str, str]]:
    """
    Uses yt-dlp to fetch trending YouTube videos for a specific region.

    Args:
        region_code (str): 2-letter country code (e.g., 'IN', 'US').
        limit (int): Number of top videos to return.

    Returns:
        List[Dict[str, str]]: List of video titles and URLs.
    """
    ydl_opts = {
        'extract_flat': True,
        'force_generic_extractor': True,
        'quiet': True,
    }

    trending_url = f"https://www.youtube.com/feed/trending?gl={region_code.upper()}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(trending_url, download=False)
            entries = info.get('entries', [])[:limit]

            return [
                {
                    "title": video.get("title", "No Title"),
                    "url": f"https://www.youtube.com/watch?v={video.get('id')}"
                }
                for video in entries
                if video.get("id")
            ]

        except Exception as e:
            print(f"❌ yt-dlp error for region '{region_code}': {e}")
            return []


@mcp.tool()
def get_yt_video_info(url: str) -> Optional[Dict[str, str]]:
    """
    Fetches detailed metadata for a specific YouTube video using yt-dlp.

    Args:
        url (str): Full URL of the YouTube video.

    Returns:
        Optional[Dict[str, str]]: Dictionary containing video metadata, or None on failure.
    """
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", ""),
                "channel": info.get("uploader", ""),
                "description": info.get("description", ""),
                "views": f"{info.get('view_count', 0):,}",
                "likes": f"{info.get('like_count', 0):,}" if info.get('like_count') is not None else "N/A",
                "upload_date": info.get("upload_date", ""),
                "duration": f"{info.get('duration', 0)} seconds",
                "thumbnail": info.get("thumbnail", ""),
                "url": info.get("webpage_url", url),
            }

        except Exception as e:
            print(f"❌ Failed to fetch video info: {e}")
            return None


@mcp.tool()
def tiktok_trending_global() -> Dict:
    """Fetches currently trending TikTok videos using a RapidAPI endpoint."""
    url = "https://tiktok-best-experience.p.rapidapi.com/trending"
    headers = {
        "x-rapidapi-key": os.getenv("tiktok"),
        "x-rapidapi-host": "tiktok-best-experience.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    return response.json()

@mcp.tool()
def parse_tiktok_data(data: Dict) -> None:
    """Parses TikTok API JSON response and prints video insights like title, stats, and hashtags."""
    try:
        if data.get("status") != "ok" or "data" not in data:
            print("❌ Error: JSON data is not valid or status is not 'ok'.")
            return
        
        video_list = data["data"].get("list", [])
        if not video_list:
            print("⚠️ No videos found in the data.")
            return
        
        print(f"\n✅ Found {len(video_list)} trending TikTok videos.\n")

        for i, video in enumerate(video_list):
            hashtags = set()
            for tag in video.get("cha_list", []):
                if tag.get("cha_name"):
                    hashtags.add(tag["cha_name"])
            for tag in video.get("text_extra", []):
                if tag.get("type") == 1 and tag.get("hashtag_name"):
                    hashtags.add(tag["hashtag_name"])

            author_info = video.get("author", {})
            title = author_info.get("nickname", "No Title Available")
            description = video.get("desc") or "No Description Provided"
            link = video.get("share_url", "No Link Available")
            
            stats = video.get("statistics", {})
            plays = stats.get("play_count", 0)
            likes = stats.get("digg_count", 0)
            comments = stats.get("comment_count", 0)
            shares = stats.get("share_count", 0)
            saves = stats.get("collect_count", 0)

            engagement_rate = 0.0
            if plays > 0:
                total_engagement = likes + comments + shares
                engagement_rate = (total_engagement / plays) * 100

            print(f"--- Video {i} ---")
            print(f"Title: {title}")
            print(f"Description: {description}")
            print(f"Link: {link}")
            print(f"Hashtags: {list(hashtags)}")
            print("\n📊 Metrics:")
            print(f"  - Plays: {plays:,}")
            print(f"  - Likes (Diggs): {likes:,}")
            print(f"  - Comments: {comments:,}")
            print(f"  - Shares: {shares:,}")
            print(f"  - Saves (Collects): {saves:,}")
            print(f"  - Engagement Rate: {engagement_rate:.2f}%")
            print("=" * 40 + "\n")

    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


@mcp.tool()
def get_this_weeks_reels_trends() -> List[Dict[str, str]]:
    """Scrapes this week’s trending Instagram Reels from Later.com."""
    url = "https://later.com/blog/instagram-reels-trends/"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        print(f"❌ Error {resp.status_code}: Unable to fetch trends")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    trends = []
    today = datetime.date.today()

    for header in soup.select("h3"):
        text = header.get_text(strip=True)
        if text.startswith("Trend:"):
            try:
                name, date_str = text[len("Trend:"):].split("—")
                trend_date = datetime.datetime.strptime(date_str.strip(), "%B %d, %Y").date()
            except ValueError:
                continue

            if (today - trend_date).days > 30:
                continue

            p_tags = header.find_next_siblings("p", limit=2)
            description = p_tags[0].get_text(strip=True) if p_tags else ""
            posts_info = p_tags[1].get_text(strip=True) if len(p_tags) > 1 else ""

            trends.append({
                "date": str(trend_date),
                "trend": name.strip(),
                "description": description,
                "posts_info": posts_info
            })

    return trends



if __name__ == "__main__":
    mcp.run()