import os
import re
import time
import requests
import xml.etree.ElementTree as ET

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
    # ВСТАВЬ СЮДА ТОКЕН НОВОГО БОТА И ID КАНАЛА
    token = "ТОКЕН_НОВОГО_БОТА_СЮДА"
    chat_id = "-100..." 
    
    text = (
        f"🌸 **Поддержка и вдохновение**\n\n"
        f"📖 **{title_ru}**\n\n"
        f"📝 {desc_ru}...\n\n"
        f"🔗 [Читать полностью]({it['link']})"
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
    print("=== Начинаем сбор постов для канала поддержки ===")
    items = fetch_rss()
    selected = items[:3] 
    
    if not selected:
        print("Свежих статей не найдено.")
        return

    for it in selected:
        print(f"Отправляем: {it['title']}")
        title_ru = translate_text(it['title'])
        desc_ru = translate_text(it['description'])
        send_to_telegram("support", it, title_ru, desc_ru)
        time.sleep(3)

if __name__ == "__main__":
    main()
