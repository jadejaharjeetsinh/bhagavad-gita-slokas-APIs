from flask import Flask, request, jsonify
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
import random
import re
from sentence_transformers import SentenceTransformer, util

load_dotenv()
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Load Gita data
with open('bhagavad_gita.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load or initialize user state
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

# Load NLP model and prepare embeddings
print("🔁 Loading sentence-transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

verse_embeddings = []
verse_map = []

for ch, ch_data in data.get("verses", {}).items():
    for verse, details in ch_data.items():
        meaning = details.get("meaning_en", "")
        if meaning:
            embedding = model.encode(meaning, convert_to_tensor=True)
            verse_embeddings.append(embedding)
            verse_map.append((ch, verse, details))

# Expanded mood keyword dictionary
MOOD_KEYWORDS = {
    "sad": ["grief", "sorrow", "sad", "depressed", "lament", "distress", "pain", "suffering"],
    "peace": ["peace", "calm", "serenity", "tranquility", "stillness", "inner peace"],
    "anger": ["anger", "wrath", "rage", "temper", "resentment", "frustration"],
    "fear": ["fear", "doubt", "anxiety", "panic", "insecurity"],
    "hope": ["hope", "faith", "courage", "bravery", "resilience", "future", "optimism"],
    "love": ["love", "affection", "compassion", "devotion", "care", "selfless"],
    "focus": ["focus", "discipline", "concentration", "determination", "dedicated"],
    "confusion": ["confused", "lost", "dilemma", "uncertain", "indecision", "unclear"],
    "stress": ["stress", "overwhelmed", "burden", "pressure", "tension"],
    "forgiveness": ["forgive", "forgiveness", "compassion", "release", "pardon", "letting go"]
}

def handle_verse_request(user_msg, user_id=None):
    user_msg = user_msg.strip().lower()

    if user_msg in ["hi", "hello", "start", "help"]:
        return (
            "🙏 Welcome to Bhagavad Gita Slok Bot!\n\n"
            "You can send:\n"
            "👉 *2.47* → Chapter 2, Verse 47\n"
            "👉 *random* → Random verse\n"
            "👉 *daily* → Verse of the day\n"
            "👉 *next* → Next verse from where you left\n"
            "👉 *peace*, *sad*, *hope*, *focus*, *stress*, etc. → Get mood-based wisdom"
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
            return "📘 You've reached the last verse of this chapter."
        return "📌 Start with a verse like *2.47* first."

    # 🔍 Mood-based wisdom (keyword and NLP)
    if user_msg in MOOD_KEYWORDS:
        keywords = MOOD_KEYWORDS[user_msg]
        matched = []
        for ch, ch_data in data.get("verses", {}).items():
            for verse, d in ch_data.items():
                if any(kw in d.get("meaning_en", "").lower() for kw in keywords):
                    matched.append((ch, verse, d))
        if matched:
            selected = random.sample(matched, min(3, len(matched)))
            return "\n".join([format_verse(ch, verse, d) for ch, verse, d in selected])

    # ✨ NLP fallback
    user_embedding = model.encode(user_msg, convert_to_tensor=True)
    results = util.semantic_search(user_embedding, verse_embeddings, top_k=3)
    best = results[0]
    return "\n".join([
        format_verse(*verse_map[hit['corpus_id']])
        for hit in best
    ])

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
