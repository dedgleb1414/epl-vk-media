import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import requests
import threading
import time
from flask import Flask, request
from services.vk_api import send_admin, publish_post, upload_photo_to_vk, upload_local_photo
from services.football_api import get_matches, get_upcoming_matches, get_leagues_menu, LEAGUES
from services.image_search import find_match_image
from services.vk_chat_poll import check_and_alert, format_score, send_to_chat, remove_voter, update_voter_list_message, delete_chat_message
from config import CHAT_PEER_ID, ADMIN_ID

app = Flask(__name__)
import os
CONFIRMATION_TOKEN = os.environ.get("CONFIRMATION_TOKEN", "0a1370a2")

CHECK_INTERVAL_SECONDS = 240

def poll_watcher_loop():
    while True:
        try:
            check_and_alert(CHAT_PEER_ID)
        except Exception as e:
            print("Ошибка фоновой проверки опроса: " + str(e))
        time.sleep(CHECK_INTERVAL_SECONDS)

threading.Thread(target=poll_watcher_loop, daemon=True).start()

state = {}
drafts = {}
match_lists = {}
selected_match = {}
photo_attachments = {}
selected_league = {}
processed_events = set()

def get_scorers(match):
    scorers = []
    try:
        details = match["competitions"][0].get("details", [])
        for d in details:
            if d.get("scoringPlay"):
                athletes = d.get("athletesInvolved", [])
                if athletes:
                    name = athletes[0]["displayName"]
                    minute = d["clock"]["displayValue"]
                    scorers.append(name + " " + minute)
    except:
        pass
    return scorers

def get_score(match):
    try:
        competitors = match["competitions"][0]["competitors"]
        home = competitors[0]
        away = competitors[1]
        home_name = home["team"]["shortDisplayName"]
        away_name = away["team"]["shortDisplayName"]
        home_score = home["score"]
        away_score = away["score"]
        return home_name + " " + home_score + ":" + away_score + " " + away_name
    except:
        return ""

def get_match_photos(match, league_code):
    photos = []
    seen_urls = set()

    def add(label, url):
        if url and url not in seen_urls:
            seen_urls.add(url)
            photos.append({"label": label, "url": url})

    summary = {}
    try:
        event_id = match.get("id")
        if event_id:
            r = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/summary",
                params={"event": event_id}, timeout=15
            )
            summary = r.json()
            images = summary.get("article", {}).get("images", [])
            for img in images:
                url = img.get("url", "")
                if url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    add("Фото матча", url)
    except Exception as e:
        print("Ошибка получения фото статьи: " + str(e))

    try:
        venue_images = summary.get("gameInfo", {}).get("venue", {}).get("images", [])
        for img in venue_images:
            add("Фото стадиона", img.get("href"))
    except Exception as e:
        print("Ошибка получения фото стадиона: " + str(e))

    try:
        details = match["competitions"][0].get("details", [])
        seen_athletes = set()
        for d in details:
            if d.get("scoringPlay"):
                for athlete in d.get("athletesInvolved", []):
                    aid = athlete["id"]
                    if aid not in seen_athletes:
                        seen_athletes.add(aid)
                        add("Фото " + athlete["displayName"], athlete.get("headshot"))
    except Exception as e:
        print("Ошибка получения фото игроков: " + str(e))

    try:
        competitors = match["competitions"][0]["competitors"]
        team_names = [c["team"]["displayName"].lower() for c in competitors]

        def mentions_team(text):
            text = (text or "").lower()
            return any(name in text for name in team_names)

        for article in summary.get("news", {}).get("articles", []):
            headline = article.get("headline", "")
            if mentions_team(headline) or mentions_team(article.get("description", "")):
                for img in article.get("images", []):
                    url = img.get("url", "")
                    if url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        add(img.get("name", "Новость турнира"), url)

        for video in summary.get("videos", []):
            if mentions_team(video.get("headline", "")):
                add(video.get("headline", "Видео-превью")[:40], video.get("thumbnail"))
    except Exception as e:
        print("Ошибка получения новостных фото: " + str(e))

    try:
        competitors = match["competitions"][0]["competitors"]
        for c in competitors:
            add("Логотип " + c["team"]["displayName"], c["team"].get("logo"))
    except Exception as e:
        print("Ошибка получения логотипов: " + str(e))

    return photos[:5]

@app.route("/", methods=["POST"])
def callback():
    data = request.json
    print("VK CALLBACK:", data)

    if data["type"] == "confirmation":
        return CONFIRMATION_TOKEN

    if data["type"] == "message_new":
        event_id = data.get("event_id", "")
        if event_id in processed_events:
            return "ok"
        processed_events.add(event_id)

        msg = data["object"]["message"]
        user_id = msg["from_id"]
        peer_id = msg.get("peer_id")
        text = msg["text"].strip()

        if peer_id == CHAT_PEER_ID and text.lower() in ("/счёт", "/счет"):
            send_to_chat(peer_id, format_score())

        elif peer_id == CHAT_PEER_ID and text.lower().startswith("/вычеркнуть"):
            if str(user_id) != str(ADMIN_ID):
                delete_chat_message(peer_id, msg.get("conversation_message_id"))
            else:
                parts = text.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    removed = remove_voter(int(parts[1]))
                    if removed:
                        update_voter_list_message(peer_id)
                    else:
                        send_to_chat(peer_id, "Неверный номер.")
                else:
                    send_to_chat(peer_id, "Напиши: /вычеркнуть <номер>")

        elif peer_id == CHAT_PEER_ID and str(user_id) != str(ADMIN_ID):
            delete_chat_message(peer_id, msg.get("conversation_message_id"))

        elif text == "/старт":
            send_admin(user_id, "EPL BOT активен")

        elif text == "/помощь":
            txt = "Команды бота:\n\n"
            txt += "/старт — проверить бота\n"
            txt += "/новости — матчи текущего тура\n"
            txt += "/пост — создать пост о матче\n"
            txt += "/стата — таблица лиги\n"
            txt += "/топ — топ бомбардиры\n"
            txt += "/новости_игроков — свежие новости\n"
            txt += "/клипы — видео с YouTube\n"
            txt += "/помощь — список команд"
            send_admin(user_id, txt)

        elif text == "/новости":
            from agents.news_agent import find_news
            news = find_news()
            send_admin(user_id, news)

        elif text == "/новости_игроков":
            send_admin(user_id, "Ищу свежие новости...")
            from agents.player_news_agent import get_news_list
            articles, txt = get_news_list()
            if not articles:
                send_admin(user_id, txt)
            else:
                match_lists[user_id] = articles
                state[user_id] = "waiting_news_choice"
                send_admin(user_id, txt + "Напиши номер новости.")

        elif text == "/топ":
            send_admin(user_id, get_leagues_menu())
            state[user_id] = "waiting_top_league"

        elif text == "/клипы":
            from agents.clips_agent import get_league_menu
            send_admin(user_id, get_league_menu())
            state[user_id] = "waiting_clip_league"

        elif text == "/стата":
            send_admin(user_id, get_leagues_menu())
            state[user_id] = "waiting_league_stats"

        elif text == "/пост":
            send_admin(user_id, "Какие матчи тебя интересуют?\n\n1. Сыгранные\n2. Предстоящие")
            state[user_id] = "waiting_match_type"

        elif state.get(user_id) == "waiting_match_type":
            if text == "1":
                selected_league[str(user_id) + "_type"] = "played"
                send_admin(user_id, get_leagues_menu())
                state[user_id] = "waiting_league"
            elif text == "2":
                selected_league[str(user_id) + "_type"] = "upcoming"
                send_admin(user_id, get_leagues_menu())
                state[user_id] = "waiting_league"
            else:
                send_admin(user_id, "Напиши 1 или 2.")

        elif state.get(user_id) == "waiting_top_league":
            if text in LEAGUES:
                league = LEAGUES[text]
                send_admin(user_id, "Загружаю топ бомбардиров...")
                from agents.scorers_agent import get_top_scorers, format_scorers, generate_scorers_posts
                from services.table_image import generate_scorers_image
                scorers = get_top_scorers(text)
                if not scorers:
                    send_admin(user_id, "Данные не найдены.")
                    state[user_id] = None
                else:
                    table = format_scorers(scorers, league["name"])
                    send_admin(user_id, table)
                    img_path = generate_scorers_image(scorers, league["name"])
                    attachment = upload_local_photo(img_path)
                    photo_attachments[user_id] = {"options": [], "chosen": [attachment] if attachment else []}
                    send_admin(user_id, "Генерирую 3 варианта поста...")
                    posts = generate_scorers_posts(scorers, league["name"])
                    drafts[user_id] = posts
                    state[user_id] = "waiting_top_post_choice"
                    txt = "Выбери вариант — напиши 1, 2 или 3:\n\n"
                    for i, p in enumerate(posts):
                        txt += "--- Вариант " + str(i+1) + " ---\n" + p + "\n\n"
                    send_admin(user_id, txt)
            else:
                send_admin(user_id, "Напиши номер лиги от 1 до 6.")

        elif state.get(user_id) == "waiting_top_post_choice":
            if text in ["1", "2", "3"]:
                posts = drafts.get(user_id, [])
                chosen = posts[int(text) - 1]
                drafts[user_id] = chosen
                state[user_id] = "waiting_top_approve"
                send_admin(user_id, "Черновик:\n\n" + chosen + "\n\nда — опубликовать с таблицей\nнет — отмена")
            else:
                send_admin(user_id, "Напиши 1, 2 или 3.")

        elif state.get(user_id) == "waiting_top_approve":
            if text.lower() == "да":
                post = drafts.get(user_id, "")
                attachments = photo_attachments.get(user_id, {}).get("chosen", [])
                attachment_str = ",".join(attachments) if attachments else None
                result = publish_post(post, attachment_str)
                if "response" in result:
                    send_admin(user_id, "Пост опубликован!")
                else:
                    send_admin(user_id, "Ошибка: " + str(result))
                state[user_id] = None
            elif text.lower() == "нет":
                state[user_id] = None
                send_admin(user_id, "Отменено.")

        elif state.get(user_id) == "waiting_clip_league":
            from agents.clips_agent import get_clips_list, LEAGUE_NAMES
            if text in LEAGUE_NAMES:
                selected_league[str(user_id) + "_clip"] = text
                send_admin(user_id, "Ищу клипы " + LEAGUE_NAMES[text] + "...")
                clips, txt = get_clips_list(user_id, text)
                if not clips:
                    send_admin(user_id, txt)
                    state[user_id] = None
                else:
                    match_lists[user_id] = clips
                    state[user_id] = "waiting_clip_choice"
                    send_admin(user_id, txt + "Напиши номер клипа.")
            else:
                send_admin(user_id, "Напиши номер лиги от 1 до 4.")

        elif state.get(user_id) == "waiting_news_choice":
            if text.isdigit():
                idx = int(text) - 1
                articles = match_lists.get(user_id, [])
                if 0 <= idx < len(articles):
                    article = articles[idx]
                    send_admin(user_id, "Генерирую пост...")
                    from agents.player_news_agent import generate_news_post
                    post, photos = generate_news_post(article)
                    drafts[user_id] = post
                    if photos:
                        photo_attachments[user_id] = {"options": [{"label": "Фото " + str(i+1), "url": p} for i, p in enumerate(photos)], "chosen": []}
                        txt = "Черновик поста:\n\n" + post + "\n\n"
                        txt += "Выбери фото (до 3 штук).\nНапиши номера через пробел, например: 1 2\n\n"
                        for i, p in enumerate(photos):
                            txt += str(i+1) + ". " + p + "\n\n"
                        txt += "0 — без фото"
                        state[user_id] = "waiting_news_photos"
                        send_admin(user_id, txt)
                    else:
                        photo_attachments[user_id] = {"options": [], "chosen": []}
                        send_admin(user_id, "Черновик:\n\n" + post + "\n\nда — опубликовать\nнет — отмена")
                        state[user_id] = "waiting_news_approve"
            else:
                send_admin(user_id, "Напиши номер цифрой.")

        elif state.get(user_id) == "waiting_news_photos":
            options = photo_attachments.get(user_id, {}).get("options", [])
            if text == "0":
                photo_attachments[user_id]["chosen"] = []
                send_admin(user_id, "Без фото.\n\nда — опубликовать\nнет — отмена")
                state[user_id] = "waiting_news_approve"
            else:
                nums = []
                for n in text.split():
                    if n.isdigit() and 1 <= int(n) <= len(options):
                        nums.append(int(n) - 1)
                nums = list(dict.fromkeys(nums))[:3]
                if nums:
                    send_admin(user_id, "Загружаю " + str(len(nums)) + " фото...")
                    attachments = []
                    for idx in nums:
                        att = upload_photo_to_vk(options[idx]["url"])
                        if att:
                            attachments.append(att)
                    photo_attachments[user_id]["chosen"] = attachments
                    send_admin(user_id, "Загружено " + str(len(attachments)) + " фото.\n\nда — опубликовать\nнет — отмена")
                    state[user_id] = "waiting_news_approve"
                else:
                    send_admin(user_id, "Неверные номера. Попробуй ещё раз.")

        elif state.get(user_id) == "waiting_news_approve":
            if text.lower() == "да":
                post = drafts.get(user_id, "")
                attachments = photo_attachments.get(user_id, {}).get("chosen", [])
                attachment_str = ",".join(attachments) if attachments else None
                result = publish_post(post, attachment_str)
                if "response" in result:
                    send_admin(user_id, "Пост опубликован!")
                else:
                    send_admin(user_id, "Ошибка: " + str(result))
                state[user_id] = None
            elif text.lower() == "нет":
                state[user_id] = None
                send_admin(user_id, "Отменено.")

        elif state.get(user_id) == "waiting_clip_choice":
            if text.isdigit():
                idx = int(text) - 1
                clips = match_lists.get(user_id, [])
                if 0 <= idx < len(clips):
                    clip = clips[idx]
                    drafts[user_id] = clip
                    state[user_id] = "waiting_clip_confirm"
                    txt = "Выбранный клип:\n\n"
                    txt += clip["title"] + "\n"
                    txt += "Канал: " + clip["channel"] + "\n\n"
                    txt += "Смотреть: " + clip["url"] + "\n\n"
                    txt += "да — скачать и опубликовать\n"
                    txt += "нет — найти другие клипы"
                    send_admin(user_id, txt)
                else:
                    send_admin(user_id, "Неверный номер.")
            else:
                send_admin(user_id, "Напиши номер цифрой.")

        elif state.get(user_id) == "waiting_clip_confirm":
            if text.lower() == "да":
                clip = drafts.get(user_id)
                send_admin(user_id, "Скачиваю видео... это займёт 1-2 минуты.")
                from services.vk_video import download_video, upload_video_to_vk
                from agents.clips_agent import generate_clip_post
                file_path = download_video(clip["url"])
                if not file_path:
                    send_admin(user_id, "Ошибка скачивания. Попробуй другой клип.")
                    state[user_id] = None
                else:
                    send_admin(user_id, "Загружаю в VK...")
                    attachment = upload_video_to_vk(file_path, clip["title"])
                    post = generate_clip_post(clip)
                    drafts[user_id] = post
                    photo_attachments[user_id] = {"options": [], "chosen": [attachment] if attachment else []}
                    state[user_id] = "waiting_clip_approve"
                    send_admin(user_id, "Черновик:\n\n" + post + "\n\nда — опубликовать\nнет — отмена")
            elif text.lower() == "нет":
                send_admin(user_id, "Ищу другие клипы...")
                from agents.clips_agent import get_clips_list
                league_key = selected_league.get(str(user_id) + "_clip", "1")
                clips, txt = get_clips_list(user_id, league_key)
                if not clips:
                    send_admin(user_id, txt)
                    state[user_id] = None
                else:
                    match_lists[user_id] = clips
                    state[user_id] = "waiting_clip_choice"
                    send_admin(user_id, txt + "Напиши номер клипа.")
            else:
                send_admin(user_id, "Напиши да или нет.")

        elif state.get(user_id) == "waiting_clip_approve":
            if text.lower() == "да":
                post = drafts.get(user_id, "")
                attachments = photo_attachments.get(user_id, {}).get("chosen", [])
                attachment_str = ",".join(attachments) if attachments else None
                result = publish_post(post, attachment_str)
                if "response" in result:
                    send_admin(user_id, "Пост с видео опубликован!")
                else:
                    send_admin(user_id, "Ошибка: " + str(result))
                state[user_id] = None
            elif text.lower() == "нет":
                state[user_id] = None
                send_admin(user_id, "Отменено.")

        elif state.get(user_id) == "waiting_league_stats":
            if text in LEAGUES:
                league = LEAGUES[text]
                send_admin(user_id, "Загружаю таблицу...")
                from agents.stats_agent import get_standings, generate_stats_post
                from services.table_image import generate_table_image
                standings = get_standings(league["code"])
                if not standings:
                    send_admin(user_id, "Таблица не найдена.")
                    state[user_id] = None
                else:
                    img_path = generate_table_image(standings, league["name"])
                    attachment = upload_local_photo(img_path)
                    send_admin(user_id, "Генерирую пост...")
                    post = generate_stats_post(standings, league["name"])
                    drafts[user_id] = post
                    photo_attachments[user_id] = {"options": [], "chosen": [attachment] if attachment else []}
                    state[user_id] = "waiting_stats_approve"
                    send_admin(user_id, "Черновик:\n\n" + post + "\n\nда — опубликовать с таблицей\nнет — отмена")
            else:
                send_admin(user_id, "Напиши номер лиги от 1 до 6.")

        elif state.get(user_id) == "waiting_stats_approve":
            if text.lower() == "да":
                post = drafts.get(user_id, "")
                attachments = photo_attachments.get(user_id, {}).get("chosen", [])
                attachment_str = ",".join(attachments) if attachments else None
                result = publish_post(post, attachment_str)
                if "response" in result:
                    send_admin(user_id, "Пост опубликован!")
                else:
                    send_admin(user_id, "Ошибка: " + str(result))
                state[user_id] = None
            elif text.lower() == "нет":
                state[user_id] = None
                send_admin(user_id, "Отменено.")

        elif state.get(user_id) == "waiting_league":
            if text in LEAGUES:
                league = LEAGUES[text]
                selected_league[user_id] = league["code"]
                match_type = selected_league.get(str(user_id) + "_type", "played")
                if match_type == "upcoming":
                    matches = get_upcoming_matches(league["code"])
                    label = "Предстоящие матчи"
                else:
                    matches = get_matches(league["code"])
                    label = "Сыгранные матчи"
                if not matches:
                    send_admin(user_id, "Матчи не найдены.")
                    state[user_id] = None
                else:
                    match_lists[user_id] = matches
                    txt = league["name"] + " — " + label + ":\n\n"
                    for i, m in enumerate(matches[:8]):
                        name = m["name"]
                        date = m["date"][:10]
                        status = m["status"]["type"]["description"]
                        txt += str(i+1) + ". " + date + "  " + name + "  [" + status + "]\n"
                    state[user_id] = "waiting_match"
                    send_admin(user_id, txt)
            else:
                send_admin(user_id, "Напиши номер лиги от 1 до 6.")

        elif state.get(user_id) == "waiting_match":
            if text.isdigit():
                idx = int(text) - 1
                matches = match_lists.get(user_id, [])
                if 0 <= idx < len(matches):
                    m = matches[idx]
                    selected_match[user_id] = m
                    match_type = selected_league.get(str(user_id) + "_type", "played")
                    send_admin(user_id, "Генерирую 3 варианта поста...")
                    name = m["name"]
                    status = m["status"]["type"]["description"]
                    headline = ""
                    try:
                        headline = m["competitions"][0]["headlines"][0]["description"]
                    except:
                        pass
                    if match_type == "upcoming":
                        date = m["date"][:10]
                        competition = m.get("season", {}).get("slug", "")
                        from services.ai_writer import write_upcoming_post, write_three_posts
                        post1 = write_upcoming_post(name, date, competition)
                        post2 = write_upcoming_post(name, date, competition)
                        post3 = write_upcoming_post(name, date, competition)
                        posts = [post1, post2, post3]
                    else:
                        scorers = get_scorers(m)
                        score = get_score(m)
                        from services.ai_writer import write_three_posts
                        posts = write_three_posts(name, status, headline, scorers, score)
                    drafts[user_id] = posts
                    state[user_id] = "waiting_post_choice"
                    txt = "Выбери вариант — напиши 1, 2 или 3:\n\n"
                    for i, p in enumerate(posts):
                        txt += "--- Вариант " + str(i+1) + " ---\n" + p + "\n\n"
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
                    txt = "Выбери картинки (до 3 штук).\nНапиши номера через пробел, например: 1 3\n\n"
                    for i, p in enumerate(photos):
                        txt += str(i+1) + ". " + p["label"] + "\n"
                    txt += "\n0 — без картинок"
                    state[user_id] = "waiting_photos"
                    send_admin(user_id, txt)
                else:
                    photo_attachments[user_id] = {"options": [], "chosen": []}
                    send_admin(user_id, "Картинки не найдены.\n\nда — опубликовать\nнет — заново")
                    state[user_id] = "waiting_approve"
            else:
                send_admin(user_id, "Напиши 1, 2 или 3.")

        elif state.get(user_id) == "waiting_photos":
            options = photo_attachments.get(user_id, {}).get("options", [])
            if text == "0":
                photo_attachments[user_id]["chosen"] = []
                send_admin(user_id, "Без картинок.\n\nда — опубликовать\nнет — заново")
                state[user_id] = "waiting_approve"
            else:
                nums = []
                for n in text.split():
                    if n.isdigit() and 1 <= int(n) <= len(options):
                        nums.append(int(n) - 1)
                nums = list(dict.fromkeys(nums))[:3]
                if nums:
                    send_admin(user_id, "Загружаю " + str(len(nums)) + " фото...")
                    attachments = []
                    for idx in nums:
                        att = upload_photo_to_vk(options[idx]["url"])
                        if att:
                            attachments.append(att)
                    photo_attachments[user_id]["chosen"] = attachments
                    send_admin(user_id, "Загружено " + str(len(attachments)) + " фото.\n\nда — опубликовать\nнет — заново")
                    state[user_id] = "waiting_approve"
                else:
                    send_admin(user_id, "Неверные номера. Попробуй ещё раз.")

        elif state.get(user_id) == "waiting_approve":
            if text.lower() == "да":
                post = drafts.get(user_id, "")
                attachments = photo_attachments.get(user_id, {}).get("chosen", [])
                attachment_str = ",".join(attachments) if attachments else None
                result = publish_post(post, attachment_str)
                if "response" in result:
                    send_admin(user_id, "Пост опубликован!")
                else:
                    send_admin(user_id, "Ошибка: " + str(result))
                state[user_id] = None
            elif text.lower() == "нет":
                send_admin(user_id, get_leagues_menu())
                state[user_id] = "waiting_league"

    return "ok"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)