import os
import re
import time
import json
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ============ НАСТРОЙКИ ============
token = os.getenv("TG_TOKEN")
chat_id = os.getenv("TG_CHAT_ID")
MYMEMORY_EMAIL = os.getenv("MYMEMORY_EMAIL", "")

SENT_FILE = "sent_news.json"

# Источники по категориям
FEEDS_EGO = [
    "https://tinybuddha.com/feed/",
    "https://bethrowles.com/category/emotions/feed/",
]

FEEDS_FIND_SELF = [
    "https://syntone.ru/feed/",
    "https://news.zerkalo.io/rss/",
]

FEEDS_BURNOUT = [
    "https://tinybuddha.com/feed/",
    "https://psi.mchs.gov.ru/rss/",
]

FEEDS_RELATIONSHIP = [
    "https://tinybuddha.com/feed/",
    "https://bethrowles.com/category/emotions/feed/",
]

# ============ ШАБЛОНЫ ОФОРМЛЕНИЯ (разные для каждого поста) ============
EGO_HEADERS = [
    "🌸 <b>Интересный факт о женском эго</b>",
    "💭 <b>А вы знали это про женское эго?</b>",
    "🪞 <b>Женское эго: неожиданный факт</b>",
]

EGO_CLOSINGS = [
    "А как у вас с этим? Пишите в комментариях 👇",
    "Знакомо? Делитесь своим опытом 💬",
    "Сохраните, чтобы подумать на досуге 🔖",
]

FIND_SELF_HEADERS = [
    "🌿 <b>Как найти себя и настроиться на дела</b>",
    "✨ <b>Потерялись? Вот что поможет</b>",
    "🧭 <b>Как вернуться к себе и своим желаниям</b>",
]

FIND_SELF_CLOSINGS = [
    "Попробуйте и расскажите, как прошло 💬",
    "Делитесь с теми, кому это сейчас нужно 🤝",
    "Ставьте ❤️, если было полезно",
]

BURNOUT_HEADERS = [
    "🔥 <b>Что делать, если выгораешь на работе</b>",
    "💆‍♀️ <b>Выгорание: как найти время на себя</b>",
    "🛑 <b>Остановитесь. Это важно</b>",
]

BURNOUT_CLOSINGS = [
    "Берегите себя. Вы важнее работы ❤️",
    "Сохраните этот пост — пригодится 🔖",
    "А как вы справляетесь с выгоранием? 👇",
]

RELATIONSHIP_HEADERS = [
    "💞 <b>Лайфхак для личной жизни</b>",
    "🌹 <b>Маленькая хитрость для отношений</b>",
    "💕 <b>Как наладить личную жизнь: один шаг</b>",
]

RELATIONSHIP_CLOSINGS = [
    "Попробуйте на этой неделе 💫",
    "Расскажите, что получилось 💬",
    "Сохраните и поделитесь с подругой 🤍",
]

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent)[-300:], f)

def translate_text(text):
    if not text:
        return text
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text[:1000], "langpair": "en|ru"}
        if MYMEMORY_EMAIL:
            params["de"] = MYMEMORY_EMAIL
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        translated = data.get('responseData', {}).get('translatedText', '')
        if "WARNING" in translated.upper() or "QUOTA" in translated.upper():
            print(f"⚠️ Лимит MyMemory: {translated[:100]}")
            return None
        return translated
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return None

def fetch_rss(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = []
        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            description = item.findtext("description") or ""
            
            image = None
            img_match = re.search(r'<img[^>]+src="([^"]+)"', description)
            if img_match:
                image = img_match.group(1)
            else:
                thumbnail = item.find("{http://search.yahoo.com/mrss/}thumbnail")
                if thumbnail is not None and thumbnail.get("url"):
                    image = thumbnail.get("url")
            
            clean_desc = re.sub(r"<[^>]+>", "", description).strip()[:300]
            items.append({
                "title": title.strip(),
                "link": link.strip(),
                "description": clean_desc,
                "image": image,
            })
        return items
    except Exception as e:
        print(f"Ошибка загрузки {url}: {e}")
        return []

def collect_from_feeds(feeds, sent):
    all_items = []
    for feed_url in feeds:
        items = fetch_rss(feed_url)
        all_items.extend(items)
        time.sleep(0.5)
    fresh = [i for i in all_items if i['link'] not in sent]
    random.shuffle(fresh)
    return fresh

def send_telegram(text, image=None):
    if not token or not chat_id:
        print("Нет TG_TOKEN или TG_CHAT_ID")
        return False
    
    if image and image.startswith("http"):
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": image, "caption": text, "parse_mode": "HTML"}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    
    r = requests.post(url, json=payload, timeout=20)
    if r.status_code == 200:
        print("✅ Отправлено")
        return True
    print(f"❌ Ошибка: {r.text}")
    return False

# ============ ГЕНЕРАТОРЫ ПОСТОВ ============
def make_ego_post(item):
    title = translate_text(item['title'])
    desc = translate_text(item['description'])
    if not title:
        return None, None
    
    header = random.choice(EGO_HEADERS)
    closing = random.choice(EGO_CLOSINGS)
    text = f"{header}\n\n{title}\n\n{desc}\n\n{closing}"
    return text, item.get('image')

def make_find_self_post(item):
    title = translate_text(item['title'])
    desc = translate_text(item['description'])
    if not title:
        return None, None
    
    header = random.choice(FIND_SELF_HEADERS)
    closing = random.choice(FIND_SELF_CLOSINGS)
    text = f"{header}\n\n{title}\n\n{desc}\n\n{closing}"
    return text, item.get('image')

def make_burnout_post(item):
    title = translate_text(item['title'])
    desc = translate_text(item['description'])
    if not title:
        return None, None
    
    header = random.choice(BURNOUT_HEADERS)
    closing = random.choice(BURNOUT_CLOSINGS)
    text = f"{header}\n\n{title}\n\n{desc}\n\n{closing}"
    return text, item.get('image')

def make_relationship_post(item):
    title = translate_text(item['title'])
    desc = translate_text(item['description'])
    if not title:
        return None, None
    
    header = random.choice(RELATIONSHIP_HEADERS)
    closing = random.choice(RELATIONSHIP_CLOSINGS)
    text = f"{header}\n\n{title}\n\n{desc}\n\n{closing}"
    return text, item.get('image')

# ============ ОСНОВНАЯ ЛОГИКА ============
def main():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    
    # 5 UTC = 8 МСК, 9 UTC = 12 МСК, 14 UTC = 17 МСК, 16 UTC = 19 МСК
    if hour not in [5, 9, 14, 16]:
        print(f"Запуск в {hour} UTC — не по расписанию")
        return
    
    print(f"=== Запуск в {hour} UTC ===")
    sent = load_sent()
    
    text = None
    image = None
    item_link = None
    
    if hour == 5:
        fresh = collect_from_feeds(FEEDS_EGO, sent)
        if not fresh:
            print("Нет постов про эго")
            return
        item = fresh[0]
        text, image = make_ego_post(item)
        item_link = item['link']
        
    elif hour == 9:
        fresh = collect_from_feeds(FEEDS_FIND_SELF, sent)
        if not fresh:
            print("Нет постов про поиск себя")
            return
        item = fresh[0]
        text, image = make_find_self_post(item)
        item_link = item['link']
        
    elif hour == 14:
        fresh = collect_from_feeds(FEEDS_BURNOUT, sent)
        if not fresh:
            print("Нет постов про выгорание")
            return
        item = fresh[0]
        text, image = make_burnout_post(item)
        item_link = item['link']
        
    elif hour == 16:
        fresh = collect_from_feeds(FEEDS_RELATIONSHIP, sent)
        if not fresh:
            print("Нет постов про отношения")
            return
        item = fresh[0]
        text, image = make_relationship_post(item)
        item_link = item['link']
    
    if not text:
        print("Не удалось сформировать пост (возможно, лимит перевода)")
        return
    
    success = send_telegram(text, image)
    
    if success and item_link:
        sent.add(item_link)
        save_sent(sent)
        print("Ссылка сохранена")

if __name__ == "__main__":
    main()
