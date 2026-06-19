import requests
from config import FOOTBALL_KEY

LEAGUE_CODES = {
    "1": {"name": "АПЛ", "id": 39},
    "2": {"name": "Ла Лига", "id": 140},
    "3": {"name": "Бундеслига", "id": 78},
    "4": {"name": "Лига 1", "id": 61},
    "5": {"name": "РПЛ", "id": 235},
    "6": {"name": "Чемпионат мира", "id": 1, "season": 2022},
}

def get_top_scorers(league_key):
    league = LEAGUE_CODES.get(league_key)
    if not league:
        return []
    try:
        url = "https://v3.football.api-sports.io/players/topscorers"
        headers = {"x-apisports-key": FOOTBALL_KEY}
        params = {"league": league["id"], "season": league.get("season", 2024)}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        data = r.json()
        print("Topscorers:", str(data)[:200])
        scorers = []
        for item in data.get("response", [])[:10]:
            player = item.get("player", {})
            stats = item.get("statistics", [{}])[0]
            name = player.get("name", "")
            team = stats.get("team", {}).get("name", "")
            goals = stats.get("goals", {}).get("total", 0) or 0
            scorers.append({"name": name, "team": team, "goals": goals})
        return scorers
    except Exception as e:
        print("Ошибка топ бомбардиров: " + str(e))
        return []

def format_scorers(scorers, league_name):
    if not scorers:
        return "Данные не найдены."
    txt = "Топ бомбардиров " + league_name + "\n\n"
    for i, s in enumerate(scorers):
        txt += str(i+1) + ". " + s["name"] + " — " + str(s["goals"]) + " голов\n"
        txt += "   " + s["team"] + "\n\n"
    return txt

def generate_scorers_post(scorers, league_name):
    from services.ai_writer import write_scorers_post
    return write_scorers_post(league_name, scorers[:3])

def generate_scorers_posts(scorers, league_name):
    from services.ai_writer import write_three_scorers_posts
    return write_three_scorers_posts(league_name, scorers[:3])