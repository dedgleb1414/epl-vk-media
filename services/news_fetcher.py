import feedparser
import requests
import re

FEEDS = [
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.theguardian.com/football/rss",
    "https://www.skysports.com/rss/12040",
]

def get_football_news(limit=5):
    articles = []
    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                photos = []

                for enc in entry.get("enclosures", []):
                    if "image" in enc.get("type", ""):
                        url = enc.get("url") or enc.get("href")
                        if url:
                            photos.append(url)

                for media in entry.get("media_content", []):
                    url = media.get("url", "")
                    if url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                        photos.append(url)

                for thumb in entry.get("media_thumbnail", []):
                    url = thumb.get("url", "")
                    if url:
                        photos.append(url)

                summary = entry.get("summary", "")
                img_urls = re.findall(r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\'<>]*)?', summary)
                photos.extend(img_urls)

                seen = set()
                unique_photos = []
                for p in photos:
                    if p not in seen:
                        seen.add(p)
                        unique_photos.append(p)

                articles.append({
                    "title": entry.get("title", ""),
                    "summary": summary[:300],
                    "link": entry.get("link", ""),
                    "source": feed.feed.get("title", ""),
                    "photos": unique_photos[:3],
                })
        except Exception as e:
            print("Ошибка RSS: " + str(e))

    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    return unique[:limit]

def get_high_quality_photo(url):
    if not url:
        return None
    url = re.sub(r'/ace/\w+/\d+/', '/ace/standard/1024/', url)
    url = re.sub(r'/standard/\d+/', '/standard/1024/', url)
    return url

def find_player_photo(title, article_photo=None):
    if article_photo:
        return get_high_quality_photo(article_photo)
    return None