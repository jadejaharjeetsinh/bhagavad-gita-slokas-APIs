# 📖 Bhagavad Gita Slokas API

A simple Flask-based REST API to query chapters and verses from the Bhagavad Gita using a structured JSON dataset.

---

## 🚀 Features

- Get verse details (text, meaning, transliteration, word meanings) from Bhagavad Gita.
- Supports querying a single or multiple verses by chapter.
- Loads data from `dataset_english.json` only once for efficient performance.

---

## 📂 Project Structure

```
your_project/
├── app.py
├── dataset_english.json
├── requirements.txt
└── README.md
```

---

## 🧰 Prerequisites

- Python 3.7+
- `pip` installed

---

## 🔧 Installation

1. Clone or download the project files.
2. Navigate to the project directory.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the API

Start the Flask server:

```bash
python app.py
```

Server will start on: `http://localhost:5000`

---

## 📡 API Endpoint

### `GET /verse-details`

#### Query Parameters:
- `chapter_number` (required): The number of the chapter (e.g., `1`, `2`, etc.)
- `verse_numbers` (required): One or more verse numbers (e.g., `1`, `2`, etc.)

#### Example Request:
```
GET /verse-details?chapter_number=1&verse_numbers=1&verse_numbers=2
```

#### Example Response:
```json
[
  {
    "chapter": "1",
    "verse": "1",
    "text": "धृतराष्ट्र उवाच |
...",
    "meaning": "Dhritarastra said: O Sanjaya, what did my sons...",
    "transliteration": "dhṛitarāśhtra uvācha...",
    "word_meanings": "dhṛitarāśhtraḥ uvācha—Dhritarashtra said..."
  },
  {
    "chapter": "1",
    "verse": "2",
    "text": "सञ्जय उवाच |
...",
    ...
  }
]
```

---

## 📄 Example CURL

```bash
curl "http://localhost:5000/verse-details?chapter_number=1&verse_numbers=1&verse_numbers=2"
```

---

## 📦 Requirements

- Flask

See `requirements.txt` for dependencies.

---

## ✅ To Do (Optional Enhancements)

- Add a POST endpoint to accept JSON body input.
- Add search by verse content.
- Create chapter summary endpoint.

---

## 🧘‍♂️ License

This project is for educational and spiritual use. Feel free to modify and share.
