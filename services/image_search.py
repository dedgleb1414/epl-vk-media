import requests

def find_match_image(match_name, league_code="eng.1"):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
        r = requests.get(url)
        events = r.json().get("events", [])

        for e in events:
            if e["name"] == match_name:
                competitors = e["competitions"][0]["competitors"]
                for c in competitors:
                    logo = c["team"].get("logo")
                    if logo:
                        return logo
    except Exception as ex:
        print(f"Ошибка поиска картинки: {ex}")

    return None