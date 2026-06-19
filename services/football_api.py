import requests
from datetime import datetime, timedelta

LEAGUES = {
    "1": {"name": "АПЛ", "code": "eng.1"},
    "2": {"name": "Ла Лига", "code": "esp.1"},
    "3": {"name": "Бундеслига", "code": "ger.1"},
    "4": {"name": "Лига 1", "code": "fra.1"},
    "5": {"name": "РПЛ", "code": "rus.1"},
    "6": {"name": "Чемпионат мира", "code": "fifa.world"},
}

def get_matches(league_code):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
    r = requests.get(url, timeout=15)
    data = r.json()
    return data.get("events", [])

def get_current_round_matches(league_code, days_back=5):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
    params = {"dates": (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d") + "-" + (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")}
    r = requests.get(url, params=params, timeout=15)
    data = r.json()
    return data.get("events", [])

def get_upcoming_matches(league_code):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
    params = {"dates": (datetime.now() + timedelta(days=1)).strftime("%Y%m%d") + "-" + (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")}
    r = requests.get(url, params=params, timeout=15)
    data = r.json()
    return data.get("events", [])

def get_leagues_menu():
    txt = "Выбери лигу:\n\n"
    for key, val in LEAGUES.items():
        txt += key + ". " + val["name"] + "\n"
    return txt