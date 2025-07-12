from flask import Flask, request, jsonify
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Load Bhagavad Gita JSON at startup
with open('bhagavad_gita.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

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

    data_in = request.get_json()
    print("== Incoming WhatsApp Webhook ==")
    print(json.dumps(data_in, indent=2))

    if data_in.get("entry"):
        for entry in data_in["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages")
                if messages:
                    msg = messages[0]
                    from_number = msg["from"]
                    user_msg = msg.get("text", {}).get("body", "").strip()

                    reply = handle_verse_request(user_msg)
                    send_message(from_number, reply)

    return "ok", 200

def handle_verse_request(user_msg):
    try:
        params = dict(item.split('=') for item in user_msg.split('&') if '=' in item)
        chapter = params.get('chapter')
        verses = params.get('verse', '').split(',')

        if not chapter or not verses:
            return "❗ Please send message as: chapter=2&verse=11 or chapter=2&verse=11,12"

        results = []
        chapter_data = data.get('verses', {}).get(str(chapter))
        if not chapter_data:
            return f"❌ Chapter {chapter} not found."

        for verse in verses:
            v = verse.strip()
            verse_detail = chapter_data.get(v)
            if verse_detail:
                results.append(f"""
                        📖 *Chapter {chapter}, Verse {v}:*
                        {verse_detail.get('text_en')}
                        
                        🗣️ _{verse_detail.get('transliteration')}_
                        
                        🇬🇧 *Meaning*: {verse_detail.get('meaning_en')}
                        
                        🧠 *Word Meanings (EN)*: {verse_detail.get('word_meanings_en')}
                        
                        🇮🇳 *Hindi Meaning*: {verse_detail.get('meaning_hi')}
                        
                        🧠 *Word Meanings (HI)*: {verse_detail.get('word_meanings_hi')}
                    """)
            else:
                results.append(f"⚠️ Verse {v} not found in chapter {chapter}.")

        return "\n".join(results[:5])  # Limit to first 5 results
    except Exception as e:
        print("Error in handle_verse_request:", str(e))
        return "⚠️ Error processing your request. Please use format:\nchapter=2&verse=11,12"

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
    response = requests.post(url, headers=headers, json=payload)
    print("Sent reply status:", response.status_code)
    print(response.text)

if __name__ == '__main__':
    app.run(debug=True)
