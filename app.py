from flask import Flask, request, jsonify
import os
import json
import random
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# Load Gita data
with open("bhagavad_gita.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Setup NLP model
model = SentenceTransformer('all-MiniLM-L6-v2')
verse_embeddings = []
verse_map = []

for ch, ch_data in data.get("verses", {}).items():
    for verse, details in ch_data.items():
        meaning = details.get("meaning_en", "")
        if meaning:
            emb = model.encode(meaning, convert_to_tensor=True)
            verse_embeddings.append(emb)
            verse_map.append((ch, verse, details))

def format_verse(ch, verse, details):
    return f"📖 Chapter {ch}, Verse {verse}:\n{details.get('text_en')}\n\nMeaning: {details.get('meaning_en')}"

@app.route("/")
def home():
    return "✅ Bhagavad Gita Bot is running!"

@app.route("/ask", methods=["GET"])
def ask():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "No query"}), 400
    emb = model.encode(query, convert_to_tensor=True)
    results = util.semantic_search(emb, verse_embeddings, top_k=3)[0]
    verses = [format_verse(*verse_map[r['corpus_id']]) for r in results]
    return "\n\n---\n\n".join(verses)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
