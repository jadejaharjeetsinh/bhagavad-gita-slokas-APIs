from flask import Flask, request, jsonify
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
import random
import re

load_dotenv()
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Load Bhagavad Gita JSON at startup
with open('bhagavad_gita.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Optional: Persist user state
USER_STATE_FILE = "user_state.json"
if os.path.exists(USER_STATE_FILE):
    with open(USER_STATE_FILE, "r") as f:
        user_last_verse = json.load(f)
else:
    user_last_verse = {}

def save_user_state():
    with open(USER_STATE_FILE, "w") as f:
        json.dump(user_last_verse, f)

def format_verse(ch, verse, verse_detail):
    return f"""\n📖 *Chapter {ch}, Verse {verse}:*
{verse_detail.get('text_en')}

🗣️ _{verse_detail.get('transliteration')}_

🇬🇧 *Meaning*: {verse_detail.get('meaning_en')}
🧠 *Word Meanings (EN)*: {verse_detail.get('word_meanings_en')}

🇮🇳 *Hindi Meaning*: {verse_detail.get('meaning_hi')}
🧠 *Word Meanings (HI)*: {verse_detail.get('word_meanings_hi')}\n"""

def handle_verse_request(user_msg, user_id=None):
    user_msg = user_msg.strip().lower()

    if user_msg in ["hi", "hello", "start", "help"]:
        return (
            "🙏 Welcome to Bhagavad Gita Slok Bot!\n\n"
            "You can send:\n"
            "👉 *2.47* → Chapter 2, Verse 47\n"
            "👉 *2.11,12* → Chapter 2, Verses 11 & 12\n"
            "👉 *random* → Random verse\n"
            "👉 *daily* → Verse of the day\n"
            "👉 *next* → Next verse after last you viewed"
        )

    if user_msg == "random":
        ch = str(random.randint(1, 18))
        ch_data = data.get("verses", {}).get(ch)
        if ch_data:
            verse = random.choice(list(ch_data.keys()))
            return format_verse(ch, verse, ch_data.get(verse))
        return "❌ Could not find a verse."

    if user_msg == "daily":
        day = datetime.now().day
        ch = str((day % 18) + 1)
        ch_data = data.get("verses", {}).get(ch)
        if ch_data:
            verse = str(((day * 2) % len(ch_data)) + 1)
            return format_verse(ch, verse, ch_data.get(verse))
        return "❌ Could not find daily verse."

    if user_msg == "next" and user_id:
        last = user_last_verse.get(user_id)
        if last:
            ch, v = map(int, last)
            v += 1
            ch_data = data.get("verses", {}).get(str(ch))
            if ch_data and str(v) in ch_data:
                user_last_verse[user_id] = (ch, v)
                save_user_state()
                return format_verse(ch, v, ch_data[str(v)])
            else:
                return "📘 You've reached the last verse of this chapter."
        return "📌 Please start with a verse like *2.47* first."

    matches = re.findall(r'(\d+)\.(\d+(?:,\d+)*)', user_msg)
    if not matches:
        return "⚠️ Please send verses like: 2.11 or 2.11,12 or 3.16,17,18"

    results = []
    for chapter, verse_group in matches:
        ch_data = data.get("verses", {}).get(str(chapter))
        if not ch_data:
            results.append(f"❌ Chapter {chapter} not found.")
            continue

        for verse in verse_group.split(','):
            verse = verse.strip()
            verse_detail = ch_data.get(verse)
            if verse_detail:
                results.append(format_verse(chapter, verse, verse_detail))
                if user_id:
                    user_last_verse[user_id] = (int(chapter), int(verse))
                    save_user_state()
            else:
                results.append(f"⚠️ Verse {verse} not found in chapter {chapter}.")

    return "\n".join(results[:5])

@app.route('/verse-details', methods=['GET'])
def get_verse_details():
    chapter = request.args.get('chapter_number')
    verses = request.args.getlist('verse_numbers')

    if not chapter or not verses:
        return jsonify({'error': 'chapter_number and verse_numbers are required'}), 400

    chapter_data = data.get('verses', {}).get(str(chapter))
    if not chapter_data:
        return jsonify({'error': f'Chapter {chapter} not found'}), 404

    results = []
    for verse in verses:
        verse_detail = chapter_data.get(verse)
        if verse_detail:
            results.append({
                'chapter': chapter,
                'verse': verse,
                'slok': verse_detail.get('text_en'),
                'transliteration': verse_detail.get('transliteration'),
                'english': {
                    'meaning': verse_detail.get('meaning_en'),
                    'word_meanings': verse_detail.get('word_meanings_en')
                },
                'hindi': {
                    'meaning': verse_detail.get('meaning_hi'),
                    'word_meanings': verse_detail.get('word_meanings_hi')
                }
            })
        else:
            results.append({
                'chapter': chapter,
                'verse': verse,
                'error': 'Verse not found'
            })

    return jsonify(results), 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Invalid verification token", 403

    data = request.get_json()
    print("== Incoming WhatsApp Webhook ==")
    print(json.dumps(data, indent=2))

    if data.get("entry"):
        for entry in data["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages")
                if messages:
                    msg = messages[0]
                    from_number = msg["from"]
                    user_msg = msg["text"]["body"]
                    reply = handle_verse_request(user_msg, from_number)
                    send_message(from_number, reply)

    return "ok", 200

def send_message(to, text):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    res = requests.post(url, headers=headers, json=payload)
    print(f"Sent reply status: {res.status_code}")
    print(res.text)

if __name__ == '__main__':
    app.run(debug=True)
