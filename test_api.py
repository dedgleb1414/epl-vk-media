import requests

url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"

r = requests.get(url)
data = r.json()

events = data.get("events", [])
print("Матчей найдено:", len(events))

for e in events[:5]:
    name = e["name"]
    date = e["date"][:10]
    status = e["status"]["type"]["description"]
    print(f"{date}  {name}  [{status}]")