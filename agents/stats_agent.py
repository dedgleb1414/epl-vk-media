import requests

def parse_entries(entries):
    standings = []
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
    return standings

def get_standings(league_code):
    url = f"https://site.api.espn.com/apis/v2/sports/soccer/{league_code}/standings"
    groups = []
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        children = data.get("children", [])
        multi_group = len(children) > 1
        for child in children:
            entries = child.get("standings", {}).get("entries", [])
            if not entries:
                continue
            name = child.get("name") if multi_group else None
            groups.append({"name": name, "teams": parse_entries(entries)})
    except Exception as e:
        print("Ошибка standings: " + str(e))
    return groups

def generate_stats_post(groups, league_name):
    from services.ai_writer import write_stats_post
    all_teams = [t for g in groups for t in g["teams"]]
    all_teams.sort(key=lambda t: t["pts"], reverse=True)
    top3 = all_teams[:3]
    bottom3 = all_teams[-3:]
    return write_stats_post(league_name, top3, bottom3)
