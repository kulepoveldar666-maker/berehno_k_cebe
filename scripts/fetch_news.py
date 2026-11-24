import os
import re
import time
import json
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ============ НАСТРОЙКИ ============
token = os.getenv("9093268140:AAHDUn5S9kg99ROBD9UMrytd0uWj5dQPlI0")
chat_id = os.getenv("-1004376020976")
MYMEMORY_EMAIL = os.getenv("kulepoveldar666@gmail.com", "")

SENT_FILE = "sent_news.json"

# Источники по категориям
NEWS_FEEDS = [
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://openai.com/news/rss.xml",
    "https://blog.google/technology/ai/rss/",
]

TIPS_FEEDS = [
    "https://www.jeffsu.org/rss/",
    "https://simonwillison.net/atom/everything/",
]

PROMPT_FEEDS = [
    "https://www.jeffsu.org/rss/",
    "https://simonwillison.net/atom/everything/",
]

BEGINNER_FEEDS = [
    "https://www.jeffsu.org/rss/",
    "https://theproductiveprompter.com/feed.xml",
]

# ============ ЗАГЛУШКИ ДЛЯ РАЗНООБРАЗИЯ ============
GREETINGS = [
    "Привет, друзья! 👋",
    "Всем привет! 🚀",
    "Доброго времени суток! ✨",
    "Приветствую! 🤖",
    "Здравствуйте! 🌟",
]

CLOSINGS = [
    "А вы что думаете? Пишите в комментариях 👇",
    "Сохраняйте, чтобы не потерять 🔖",
    "Попробуйте и расскажите, как прошло 💬",
    "Делитесь с теми, кому это пригодится 🤝",
    "Ставьте реакцию, если было полезно ❤️",
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
        print("Нет токена или chat_id")
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

# ============ ГЕНЕРАТОРЫ ПОСТОВ (РАЗНЫЕ ШАБЛОНЫ) ============
def make_news_post(item):
    """Глобальные новости ИИ"""
    title = translate_text(item['title'])
    desc = translate_text(item['description'])
    if not title:
        return None
    
    greeting = random.choice(GREETINGS)
    closing = random.choice(CLOSINGS)
    
    templates = [
        f"{greeting}\n\n🤖 <b>{title}</b>\n\n{desc}\n\n{closing}",
        f"{greeting}\n\nЧто нового в мире ИИ?\n\n🔥 <b>{title}</b>\n\n{desc}\n\n{closing}",
        f"{greeting}\n\n<b>{title}</b>\n\n{desc}\n\n{closing}",
    ]
    return random.choice(templates)

def make_tips_post(item):
    """Полезные лайфхаки"""
    title = translate_text(item['title'])
    desc = translate_text(item['description'])
    if not title:
        return None
    
    greeting = random.choice(GREETINGS)
    closing = random.choice(CLOSINGS)
    
    templates = [
        f"{greeting}\n\n💡 <b>Лайфхак дня</b>\n\n{title}\n\n{desc}\n\n{closing}",
        f"{greeting}\n\n<b>{title}</b>\n\n{desc}\n\n{closing}",
        f"{greeting}\n\n📌 <b>Полезно знать</b>\n\n{title}\n\n{desc}\n\n{closing}",
    ]
    return random.choice(templates)

def make_prompt_post():
    """Промпт для новичков — генерируется из шаблонов"""
    prompts = [
        {
            "title": "Промпт для объяснения сложных тем простыми словами",
            "body": "Скопируй и вставь в ChatGPT:\n\n<i>«Объясни [тема] так, будто мне 10 лет. Используй простые примеры из жизни. Без сложных терминов.»</i>\n\nЗамени [тема] на что угодно — нейросети, квантовые компьютеры, блокчейн."
        },
        {
            "title": "Промпт для составления плана обучения",
            "body": "Скопируй и вставь:\n\n<i>«Составь план изучения [навык] на 30 дней. Каждый день — одна конкретная задача на 30 минут. Учитывай, что я полный новичок.»</i>\n\nОтлично работает для любого навыка."
        },
        {
            "title": "Промпт для проверки текста",
            "body": "Скопируй и вставь:\n\n<i>«Проверь этот текст на ошибки и стиль. Предложи 3 варианта улучшения. Не меняй смысл.»</i>\n\nВставь свой текст после этой фразы."
        },
        {
            "title": "Промпт для генерации идей",
            "body": "Скопируй и вставь:\n\n<i>«Дай мне 10 идей для [проект/статья/бизнес]. Раздели на: простые (1 день), средние (1 неделя), сложные (1 месяц).»</i>\n\nРаботает для чего угодно."
        },
    ]
    p = random.choice(prompts)
    greeting = random.choice(GREETINGS)
    closing = random.choice(CLOSINGS)
    
    templates = [
        f"{greeting}\n\n🎯 <b>{p['title']}</b>\n\n{p['body']}\n\n{closing}",
        f"{greeting}\n\n<b>{p['title']}</b>\n\n{p['body']}\n\n{closing}",
    ]
    return random.choice(templates)

def make_beginner_post(item):
    """Лайфхаки для начинающих"""
    title = translate_text(item['title'])
    desc = translate_text(item['description'])
    if not title:
        return None
    
    greeting = random.choice(GREETINGS)
    closing = random.choice(CLOSINGS)
    
    templates = [
        f"{greeting}\n\n🌱 <b>Для начинающих</b>\n\n{title}\n\n{desc}\n\n{closing}",
        f"{greeting}\n\n<b>{title}</b>\n\n{desc}\n\n{closing}",
        f"{greeting}\n\n🚀 <b>С чего начать?</b>\n\n{title}\n\n{desc}\n\n{closing}",
    ]
    return random.choice(templates)

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
        # 08:00 МСК — глобальные новости
        fresh = collect_from_feeds(NEWS_FEEDS, sent)
        if not fresh:
            print("Нет новостей")
            return
        item = fresh[0]
        text = make_news_post(item)
        image = item.get('image')
        item_link = item['link']
        
    elif hour == 9:
        # 12:00 МСК — полезные лайфхаки
        fresh = collect_from_feeds(TIPS_FEEDS, sent)
        if not fresh:
            print("Нет лайфхаков")
            return
        item = fresh[0]
        text = make_tips_post(item)
        image = item.get('image')
        item_link = item['link']
        
    elif hour == 14:
        # 17:00 МСК — промпт для новичков
        text = make_prompt_post()
        
    elif hour == 16:
        # 19:00 МСК — лайфхаки для начинающих
        fresh = collect_from_feeds(BEGINNER_FEEDS, sent)
        if not fresh:
            print("Нет постов для начинающих")
            return
        item = fresh[0]
        text = make_beginner_post(item)
        image = item.get('image')
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
