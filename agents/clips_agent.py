from services.youtube_api import search_football_clips

LEAGUE_QUERIES = {
    "1": [
        "Premier League official highlights 2026",
        "Premier League goals this week 2026",
        "EPL match highlights 2026",
    ],
    "2": [
        "РПЛ обзор матча 2026",
        "Российская Премьер Лига голы 2026",
        "РПЛ лучшие моменты 2026",
    ],
    "3": [
        "La Liga official highlights 2026",
        "LaLiga goals 2026",
        "La Liga mejores goles 2026",
    ],
}

LEAGUE_NAMES = {
    "1": "АПЛ",
    "2": "РПЛ",
    "3": "Ла Лига",
}

current_query_index = {}

def get_league_menu():
    txt = "Выбери лигу для поиска клипов:\n\n"
    for key, name in LEAGUE_NAMES.items():
        txt += key + ". " + name + "\n"
    return txt

def get_clips_list(user_id=None, league_key="1"):
    queries = LEAGUE_QUERIES.get(league_key, LEAGUE_QUERIES["1"])
    idx = current_query_index.get(str(user_id) + "_" + league_key, 0)
    query = queries[idx % len(queries)]
    current_query_index[str(user_id) + "_" + league_key] = idx + 1

    clips = search_football_clips(query, max_results=5)
    if not clips:
        return None, "Клипы не найдены."

    league_name = LEAGUE_NAMES.get(league_key, "")
    txt = league_name + " — найденные клипы:\n\n"
    for i, c in enumerate(clips):
        txt += str(i+1) + ". " + c["title"] + "\n"
        txt += "   [" + c["channel"] + "]\n\n"

    return clips, txt

def generate_clip_post(clip):
    from services.ai_writer import write_clip_post
    post = write_clip_post(clip["title"])
    return post