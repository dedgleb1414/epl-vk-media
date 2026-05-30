import requests
from config import YOUTUBE_KEY

def search_football_clips(query="Premier League highlights", max_results=5):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoDuration": "short",
        "order": "date",
        "maxResults": max_results,
        "key": YOUTUBE_KEY,
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    clips = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        thumb = item["snippet"]["thumbnails"]["high"]["url"]
        clips.append({
            "id": video_id,
            "title": title,
            "channel": channel,
            "url": "https://www.youtube.com/watch?v=" + video_id,
            "thumb": thumb,
        })
    return clips