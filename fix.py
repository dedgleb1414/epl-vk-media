content = '''from flask import Flask, request
from services.vk_api import send_admin, publish_post, upload_photo_to_vk
from services.football_api import get_matches, get_leagues_menu, LEAGUES
from services.image_search import find_match_image

app = Flask(__name__)
CONFIRMATION_TOKEN = "30d8d81b"

state = {}
drafts = {}
match_lists = {}
selected_match = {}
photo_attachments = {}
selected_league = {}
processed_events = set()

@app.route("/", methods=["POST"])
def callback():
    data = request.json
    print(data)

    if data["type"] == "confirmation":
        return CONFIRMATION_TOKEN

    if data["type"] == "message_new":
        event_id = data.get("event_id", "")
        if event_id in processed_events:
            return "ok"
        processed_events.add(event_id)

        msg = data["object"]["message"]
        user_id = msg["from_id"]
        text = msg["text"].strip()

        if text == "/старт":
            send_admin(user_id, "EPL BOT активен")

        elif text == "/новости":
            from agents.news_agent import find_news
            news = find_news()
            send_admin(user_id, news)

        elif text == "/пост":
            send_admin(user_id, get_leagues_menu())
            state[user_id] = "waiting_league"

        elif state.get(user_id) == "waiting_league":
            if text in LEAGUES:
                league = LEAGUES[text]
                selected_league[user_id] = league["code"]
                matches = get_matches(league["code"])
                if not matches:
                    send_admin(user_id, f"Матчи не найдены в {league[\'name\']}.")
                    state[user_id] = None
                else:
                    match_lists[user_id] = matches
                    txt = f"{league[\'name\']} — выбери матч:\\n\\n"
                    for i, m in enumerate(matches[:8]):
                        name = m["name"]
                        date = m["date"][:10]
                        status = m["status"]["type"]["description"]
                        txt += f"{i+1}. {date}  {name}  [{status}]\\n"
                    state[user_id] = "waiting_match"
                    send_admin(user_id, txt)
            else:
                send_admin(user_id, "Напиши номер лиги от 1 до 5.")

        elif state.get(user_id) == "waiting_match":
            if text.isdigit():
                idx = int(text) - 1
                matches = match_lists.get(user_id, [])
                if 0 <= idx < len(matches):
                    m = matches[idx]
                    selected_match[user_id] = m
                    send_admin(user_id, "Генерирую 3 варианта поста...")
                    name = m["name"]
                    status = m["status"]["type"]["description"]
                    headline = ""
                    try:
                        headline = m["competitions"][0]["headlines"][0]["description"]
                    except:
                        pass
                    scorers = get_scorers(m)
                    from services.ai_writer import write_three_posts
                    posts = write_three_posts(name, status, headline, scorers)
                    drafts[user_id] = posts
                    state[user_id] = "waiting_post_choice"
                    txt = "Выбери вариант поста — напиши 1, 2 или 3:\\n\\n"
                    for i, p in enumerate(posts):
                        txt += f"--- Вариант {i+1} ---\\n{p}\\n\\n"
                    send_admin(user_id, txt)
                else:
                    send_admin(user_id, "Неверный номер. Попробуй ещё раз.")
            else:
                send_admin(user_id, "Напиши номер матча цифрой.")

        elif state.get(user_id) == "waiting_post_choice":
            if text in ["1", "2", "3"]:
                posts = drafts.get(user_id, [])
                chosen = posts[int(text) - 1]
                drafts[user_id] = chosen
                league_code = selected_league.get(user_id, "eng.1")
                m = selected_match.get(user_id)
                photos = get_match_photos(m, league_code)
                if photos:
                    photo_attachments[user_id] = {"options": photos, "chosen": []}
                    txt = "Выбери картинки (до 3 штук).\\nНапиши номера через пробел, например: 1 3 5\\n\\n"
                    for i, p in enumerate(photos):
                        txt += f"{i+1}. {p[\'label\']}\\n"
                    txt += "\\n0 — без картинок"
                    state[user_id] = "waiting_photos"
                    send_admin(user_id, txt)
                else:
                    photo_attachments[user_id] = {"options": [], "chosen": []}
                    send_admin(user_id, f"Картинки не найдены.\\n\\n✅ — опубликовать\\n❌ — переделать")
                    state[user_id] = "waiting_approve"
            else:
                send_admin(user_id, "Напиши 1, 2 или 3.")