from flask import Flask, request, jsonify
import json

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Load the merged JSON file once at startup
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

if __name__ == '__main__':
    app.run(debug=True)
