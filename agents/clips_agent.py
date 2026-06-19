from services.youtube_api import search_football_clips, LEAGUE_SEARCH
from services.football_api import get_matches

LEAGUE_NAMES = {
    "1": "АПЛ",
    "2": "РПЛ",
    "3": "Ла Лига",
    "4": "Чемпионат мира",
}

LEAGUE_CODES = {
    "1": "eng.1",
    "2": "rus.1",
    "3": "esp.1",
    "4": "fifa.world",
}

current_query_index = {}

def get_league_menu():
    txt = "Выбери лигу для поиска клипов:\n\n"
    for key, name in LEAGUE_NAMES.items():
        txt += key + ". " + name + "\n"
    return txt

def build_match_queries(league_key):
    code = LEAGUE_CODES.get(league_key, "eng.1")
    try:
        matches = get_matches(code)
    except Exception as e:
        print("Ошибка получения матчей для клипов: " + str(e))
        matches = []

    queries = []
    for m in matches:
        try:
            competitors = m["competitions"][0]["competitors"]
            home = competitors[0]["team"]["shortDisplayName"]
            away = competitors[1]["team"]["shortDisplayName"]
            queries.append(home + " " + away + " обзор голы")
        except Exception:
            continue
    return queries

def get_clips_list(user_id=None, league_key="1"):
    match_queries = build_match_queries(league_key)
    queries = match_queries if match_queries else LEAGUE_SEARCH.get(league_key, LEAGUE_SEARCH["1"])

    idx = current_query_index.get(str(user_id) + "_" + league_key, 0)
    query = queries[idx % len(queries)]
    current_query_index[str(user_id) + "_" + league_key] = idx + 1

    clips = search_football_clips(query, max_results=5)
    if not clips:
        return None, "Клипы не найдены."

    league_name = LEAGUE_NAMES.get(league_key, "")
    txt = league_name + " — найденные клипы (" + query + "):\n\n"
    for i, c in enumerate(clips):
        txt += str(i+1) + ". " + c["title"] + "\n"
        txt += "   Длительность: " + c["duration"] + "\n\n"

    return clips, txt

def generate_clip_post(clip):
    from services.ai_writer import write_clip_post
    post = write_clip_post(clip["title"])
    return post
