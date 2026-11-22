import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

RSS_URL = "https://tinybuddha.com/feed/"

def translate_text(text):
    if not text:
        return text
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "en|ru"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data['responseData']['translatedText']
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text

def fetch_rss():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(RSS_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        description = item.findtext("description") or ""
        
        img_match = re.search(r'<img[^>]+src="([^"]+)"', description)
        image = img_match.group(1) if img_match else "Картинка не найдена в RSS"
        
        clean_desc = re.sub(r"<[^>]+>", "", description).strip()[:300]
        
        items.append({
            "title": title.strip(),
            "link": link.strip(),
            "description": clean_desc,
            "image": image,
        })
    return items

def send_to_telegram(category, it, title_ru, desc_ru):
    # ВСТАВЬ 
    token = "9093268140:AAHDUn5S9kg99ROBD9UMrytd0uWj5dQPlI0"
    chat_id = "-1004376020976" 
    

    text = (
        f"🌸 **Поддержка и вдохновение**\n\n"
        f"📖 **{title_ru}**\n\n"
        f"📝 {desc_ru}..."
    )
    
    if it['image'] and "http" in it['image']:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": it['image'],
            "caption": text,
            "parse_mode": "Markdown"
        }
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Пост успешно отправлен!")
    else:
        print(f"Ошибка отправки: {response.text}")

def main():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    
    print(f"=== Запуск в {hour} UTC ===")
    items = fetch_rss()
    
    # Берем 
    selected = items[:3]
    
    if not selected:
        print("Свежих статей не найдено.")
        return

    
    if hour == 5:

        it = selected[0]
        print(f"Отправляем 1-й пост: {it['title']}")
        title_ru = translate_text(it['title'])
        desc_ru = translate_text(it['description'])
        send_to_telegram("support", it, title_ru, desc_ru)
        
    elif hour == 9:
        
        it = selected[1]
        print(f"Отправляем 2-й пост: {it['title']}")
        title_ru = translate_text(it['title'])
        desc_ru = translate_text(it['description'])
        send_to_telegram("support", it, title_ru, desc_ru)
        
    elif hour == 14:
        
        it = selected[2]
        print(f"Отправляем 3-й пост: {it['title']}")
        title_ru = translate_text(it['title'])
        desc_ru = translate_text(it['description'])
        send_to_telegram("support", it, title_ru, desc_ru)
        
    else:
        print(f"Запуск в {hour} UTC не соответствует расписанию. Ждем следующего.")

if __name__ == "__main__":
    main()
