import requests
from config import USER_TOKEN

LEAGUE_SEARCH = {
    "1": ["АПЛ обзор матча", "Premier League highlights", "английская премьер лига голы"],
    "2": ["РПЛ обзор матча", "российская премьер лига голы", "РПЛ лучшие моменты"],
    "3": ["Ла Лига обзор матча", "La Liga highlights", "испанская лига голы"],
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
            "access_token": USER_TOKEN,
            "v": "5.199"
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        print("VK video search:", str(data)[:200])

        clips = []
        items = data.get("response", {}).get("items", [])
        for item in items:
            owner_id = item.get("owner_id")
            video_id = item.get("id")
            title = item.get("title", "")
            duration = item.get("duration", 0)
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