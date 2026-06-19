import re
from services.news_fetcher import get_football_news, get_high_quality_photo, scrape_article_images

def image_identity(url):
    m = re.search(r'([0-9a-f]{4}/live/[0-9a-f-]+)', url)
    return m.group(1) if m else url

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

    photos = []
    seen = set()
    for p in article.get("photos", []):
        hq = get_high_quality_photo(p)
        ident = image_identity(hq) if hq else None
        if hq and ident not in seen:
            seen.add(ident)
            photos.append(hq)

    if len(photos) < 5:
        for url in scrape_article_images(article.get("link"), limit=15):
            ident = image_identity(url)
            if ident not in seen:
                seen.add(ident)
                photos.append(url)
            if len(photos) >= 5:
                break

    return post, photos[:5]