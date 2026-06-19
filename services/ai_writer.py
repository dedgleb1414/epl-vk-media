from groq import Groq
from config import GROQ_KEY

client = Groq(api_key=GROQ_KEY)

def write_three_posts(match_name, status, headline="", scorers=None, score=""):
    scorers_text = ""
    if scorers:
        scorers_text = "Голы: " + ", ".join(scorers)

    score_line = f"Счёт: {score}" if score else ""

    prompt = f"""Ты редактор спортивного VK сообщества.
Напиши 3 разных варианта поста на русском про матч:
{match_name} [{status}]
{score_line}
{f'Заголовок: {headline}' if headline else ''}
{scorers_text}

Требования:
- Начни пост со счёта матча, например: Арсенал 2:1 Челси
- Затем на отдельных строках кто забил и на какой минуте
- Затем 2-3 предложения текста
- Используй эмодзи
- Стиль живой и эмоциональный
- НЕ пиши "Вариант 1", "Вариант 2" и т.д.
- Разделяй варианты строкой ---

Формат каждого варианта:
[счёт]
[голы по строкам]

[текст поста]"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900
    )
    raw = response.choices[0].message.content
    parts = raw.split("---")
    posts = []
    for p in parts:
        clean = p.strip()
        if len(clean) > 30:
            posts.append(clean)
    while len(posts) < 3:
        posts.append(posts[0] if posts else raw)
    return posts[:3]

def write_post(match_name, status, headline=""):
    posts = write_three_posts(match_name, status, headline)
    return posts[0]
def write_stats_post(league_name, top3, bottom3):
    top_text = ", ".join([f"{s['team']} ({s['pts']} очков)" for s in top3])
    bottom_text = ", ".join([f"{s['team']} ({s['pts']} очков)" for s in bottom3])

    prompt = f"""Ты редактор спортивного VK сообщества.
Напиши короткий пост на русском про турнирную таблицу {league_name}.
Топ-3: {top_text}
Аутсайдеры: {bottom_text}
Требования:
- 3-4 предложения
- Используй эмодзи
- Упомяни лидера и борьбу за выживание
- Стиль живой и эмоциональный"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content

def write_news_post(title, summary):
    prompt = f"""Ты редактор спортивного VK сообщества о футболе.
Напиши пост на русском языке по этой новости:
Заголовок: {title}
Детали: {summary}

Требования:
- 3-4 предложения
- Используй эмодзи
- Стиль живой и эмоциональный
- Не копируй заголовок дословно"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content
def write_clip_post(title):
    prompt = "Ты редактор спортивного VK сообщества о футболе.\nНапиши короткий пост на русском для видео: " + title + "\nТребования:\n- 2-3 предложения\n- Используй эмодзи\n- Стиль живой и эмоциональный\n- Призыв смотреть видео"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return response.choices[0].message.content

def write_scorers_post(league_name, top3):
    names = ", ".join([s["name"] + " (" + str(s["goals"]) + " голов)" for s in top3])
    prompt = "Ты редактор спортивного VK сообщества.\nНапиши пост на русском про топ бомбардиров " + league_name + ".\nЛидеры: " + names + "\nТребования:\n- 3-4 предложения\n- Используй эмодзи\n- Стиль живой и эмоциональный"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content

def write_three_scorers_posts(league_name, top3):
    names = ", ".join([s["name"] + " (" + str(s["goals"]) + " голов)" for s in top3])
    prompt = ("Ты редактор спортивного VK сообщества.\n"
              "Напиши 3 разных варианта поста на русском про топ бомбардиров " + league_name + ".\n"
              "Лидеры: " + names + "\n"
              "Требования:\n"
              "- 3-4 предложения\n"
              "- Используй эмодзи\n"
              "- Стиль живой и эмоциональный\n"
              "- НЕ пиши \"Вариант 1\" и т.д.\n"
              "- Разделяй варианты строкой ---")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900
    )
    raw = response.choices[0].message.content
    parts = raw.split("---")
    posts = []
    for p in parts:
        clean = p.strip()
        if len(clean) > 20:
            posts.append(clean)
    while len(posts) < 3:
        posts.append(posts[0] if posts else raw)
    return posts[:3]

def write_upcoming_post(match_name, date, competition):
    prompt = "Ты редактор спортивного VK сообщества.\nНапиши анонс матча на русском:\n" + match_name + "\nДата: " + date + "\nТурнир: " + competition + "\nТребования:\n- 3-4 предложения\n- Используй эмодзи\n- Стиль живой и эмоциональный\n- Призыв следить за матчем"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content