import requests

def get_standings(league_code):
    url = f"https://site.api.espn.com/apis/v2/sports/soccer/{league_code}/standings"
    r = requests.get(url)
    data = r.json()
    standings = []
    try:
        entries = data["children"][0]["standings"]["entries"]
        for e in entries:
            team = e["team"]["shortDisplayName"]
            stats = {}
            for s in e["stats"]:
                try:
                    stats[s["name"]] = float(s["value"])
                except:
                    pass
            standings.append({
                "team": team,
                "gp": int(stats.get("gamesPlayed", 0)),
                "w": int(stats.get("wins", 0)),
                "d": int(stats.get("ties", 0)),
                "l": int(stats.get("losses", 0)),
                "gf": int(stats.get("pointsFor", 0)),
                "ga": int(stats.get("pointsAgainst", 0)),
                "gd": int(stats.get("pointDifferential", 0)),
                "pts": int(stats.get("points", 0)),
            })
    except Exception as e:
        print("Ошибка standings: " + str(e))
    return standings

def generate_stats_post(standings, league_name):
    from services.ai_writer import write_stats_post
    top3 = standings[:3]
    bottom3 = standings[-3:]
    return write_stats_post(league_name, top3, bottom3)