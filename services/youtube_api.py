import requests
from config import USER_TOKEN

LEAGUE_SEARCH = {
    "1": ["АПЛ голы обзор", "Premier League goals highlights", "английская премьер лига лучшие моменты"],
    "2": ["РПЛ голы обзор", "российская премьер лига голы", "РПЛ лучшие моменты"],
    "3": ["Ла Лига голы обзор", "La Liga goals highlights", "испанская лига лучшие моменты"],
}

def search_football_clips(query, max_results=5):
    try:
        url = "https://api.vk.com/method/video.search"
        params = {
            "q": query,
            "count": max_results,
            "sort": 0,
            "hd": 1,
            "filters": "youtube",
            "shorter": 600,
            "access_token": USER_TOKEN,
            "v": "5.199"
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        print("VK video search:", str(data)[:200])

        clips = []
        items = data.get("response", {}).get("items", [])
        for item in items:
            duration = item.get("duration", 0)
            if duration <= 0:
                continue
            owner_id = item.get("owner_id")
            video_id = item.get("id")
            title = item.get("title", "")
            clips.append({
                "id": str(owner_id) + "_" + str(video_id),
                "title": title,
                "channel": item.get("description", "")[:50],
                "url": "https://vk.com/video" + str(owner_id) + "_" + str(video_id),
                "attachment": "video" + str(owner_id) + "_" + str(video_id),
                "duration": str(duration // 60) + ":" + str(duration % 60).zfill(2),
            })
        return clips
    except Exception as e:
        print("Ошибка поиска VK видео: " + str(e))
        return []