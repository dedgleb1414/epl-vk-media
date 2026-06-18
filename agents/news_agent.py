from services.football_api import get_matches
from services.ai_writer import write_post

def find_news():
    matches = get_matches("eng.1")

    if not matches:
        return "Матчи не найдены."

    txt = "Матчи АПЛ:\n\n"
    for m in matches:
        name = m["name"]
        date = m["date"][:10]
        status = m["status"]["type"]["description"]
        txt += f"{date}  {name}  [{status}]\n"

    return txt

def generate_post(match_index=0):
    matches = get_matches("eng.1")

    if not matches:
        return "Матчи не найдены."

    m = matches[match_index]
    name = m["name"]
    status = m["status"]["type"]["description"]

    headline = ""
    try:
        headline = m["competitions"][0]["headlines"][0]["description"]
    except:
        pass

    return write_post(name, status, headline)