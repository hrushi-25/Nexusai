# ============================================================
#  NexusAI — Flask Backend
# ============================================================
import os, uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from chatbot_logic import get_response
from firebase_service import save_message, get_chat_history
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-dev-secret")

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/chat")
def chat_page():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data or not data.get("message"):
        return jsonify({"error": "No message provided"}), 400

    user_message = data["message"].strip()
    session_id   = data.get("session_id") or str(uuid.uuid4())
    memory       = data.get("memory", [])   # ← conversation memory from frontend

    save_message(session_id, role="user", message=user_message)
    bot_response = get_response(user_message, memory=memory)
    save_message(session_id, role="bot",  message=bot_response)

    return jsonify({"response": bot_response, "session_id": session_id})

@app.route("/api/health")
def health():
    return jsonify({"status":"ok","service":"NexusAI","timestamp":datetime.utcnow().isoformat()+"Z"})

@app.route("/api/history/<session_id>")
def history(session_id):
    return jsonify({"session_id": session_id, "messages": get_chat_history(session_id)})

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG","false").lower()=="true", host="0.0.0.0", port=5000)
