# 🚀 Whats Trending On Social Media - FastAPI Server

This FastAPI server fetches trending data from platforms like **YouTube**, **TikTok**, and **Instagram Reels** using various scraping and API techniques.

## 🛠️ Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

## 🚀 Running the Server

Start the FastAPI server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload
```

The server will run on `http://localhost:8000`.

## 📚 API Endpoints

### YouTube Endpoints

- **GET /youtube/comments/{video_id}**
  - Fetch YouTube comments for a video
  - Query params: `max_comments` (default: 100)

- **GET /youtube/trending/global**
  - Get globally trending YouTube videos
  - Query params: `limit` (default: 10)

- **GET /youtube/trending/{region_code}**
  - Get trending YouTube videos by region
  - Query params: `limit` (default: 10)

- **GET /youtube/video-info**
  - Get metadata for a YouTube video
  - Query params: `url` (required)

### TikTok Endpoints

- **GET /tiktok/trending**
  - Get trending TikTok videos summary
  - Requires `tiktok` environment variable with RapidAPI key

### Instagram Endpoints

- **GET /instagram/reels/trends**
  - Get this week's Instagram Reels trends

## 🌐 Interactive API Docs

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## 📎 Notes

- YouTube comment extraction uses unofficial scraping and may break with YouTube changes.
- TikTok API requires a valid RapidAPI key set as `tiktok` environment variable.
- Instagram scraping is done by parsing Later.com's blog – may vary if structure changes.

## 🧑‍💻 Author

Converted from MCP server by Trends-MCP