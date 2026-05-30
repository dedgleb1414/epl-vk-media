from services.news_fetcher import get_football_news, get_high_quality_photo

def get_news_list():
    articles = get_football_news(5)
    if not articles:
        return None, "Новости не найдены."

    txt = "Свежие футбольные новости:\n\n"
    for i, a in enumerate(articles):
        count = len(a.get("photos", []))
        photo_mark = " 🖼" + str(count) if count > 0 else ""
        txt += str(i+1) + ". " + a["title"] + photo_mark + "\n"
        txt += "   [" + a["source"] + "]\n\n"

    return articles, txt

def generate_news_post(article):
    from services.ai_writer import write_news_post
    post = write_news_post(article["title"], article["summary"])
    photos = [get_high_quality_photo(p) for p in article.get("photos", []) if p]
    return post, photos