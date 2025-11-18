from flask import Flask, request, jsonify, send_from_directory
import os, json, requests
from dotenv import load_dotenv
from difflib import SequenceMatcher

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL")

app = Flask(__name__)

# --------------------------- LOAD FAQ KB ---------------------------
try:
    with open("data.json", "r", encoding="utf-8") as f:
        KB = json.load(f)
except:
    KB = {}

# --------------------------- LOAD DEPARTMENTS ---------------------------
try:
    with open("departments.json", "r", encoding="utf-8") as f:
        DEPARTMENTS = json.load(f)
except:
    DEPARTMENTS = {}

# --------------------------- HELPERS ---------------------------

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_in_kb(query):
    query = query.lower()
    for key, answer in KB.items():
        if key in query:
            return answer
        
        if similarity(query, key) > 0.65:
            return answer
    return None

def find_department(query):
    query = query.lower()
    for dept, info in DEPARTMENTS.items():
        for kw in info["keywords"]:
            if kw in query:
                return info["response"]
            if similarity(query, kw) > 0.70:
                return info["response"]
    return None

def ask_gemini(prompt, history):
    try:
        formatted_history = ""

        for msg in history[-10:]:
            if msg["sender"] == "user":
                formatted_history += f"User: {msg['text']}\n"
            else:
                formatted_history += f"Bot: {msg['text']}\n"

        full_prompt = f"{formatted_history}\nUser: {prompt}\nBot:"

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"parts": [{"text": full_prompt}]}
            ]
        }

        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload
        )

        data = response.json()

        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]

        return "I couldn't get a proper response."

    except Exception as e:
        return f"Gemini Error: {str(e)}"


# --------------------------- ROUTES ---------------------------

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(".", filename)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Empty message"}), 400

    # 1️⃣ FAQ database
    kb_ans = find_in_kb(message)
    if kb_ans:
        return jsonify({"answer": kb_ans, "source": "faq"}), 200

    # 2️⃣ Department routing
    dept_ans = find_department(message)
    if dept_ans:
        return jsonify({"answer": dept_ans, "source": "department"}), 200

    # 3️⃣ Gemini AI with chat memory
    gemini_ans = ask_gemini(message, history)
    return jsonify({"answer": gemini_ans, "source": "gemini"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
