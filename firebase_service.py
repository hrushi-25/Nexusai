# ============================================================
#  firebase_service.py
#  Firebase Admin SDK — Firestore read/write wrapper.
#  Called by app.py to save and retrieve chat messages.
# ============================================================

import os
import json
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

# ── Lazy-load Firebase to avoid crash if credentials missing ─
_db = None

def _get_db():
    """
    Initialise Firebase Admin SDK once and return Firestore client.
    Reads credentials from FIREBASE_CREDENTIALS_JSON env variable
    (a JSON string of your serviceAccountKey.json contents).
    """
    global _db
    if _db is not None:
        return _db

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

        if not cred_json:
            print("[Firebase] ⚠ FIREBASE_CREDENTIALS_JSON not set. Firebase disabled.")
            return None

        cred_dict = json.loads(cred_json)

        # Avoid re-initialising if already done (e.g. Flask reloader)
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)

        _db = firestore.client()
        print("[Firebase] ✅ Connected to Firestore.")
        return _db

    except ImportError:
        print("[Firebase] ⚠ firebase-admin not installed. Run: pip install firebase-admin")
        return None
    except Exception as e:
        print(f"[Firebase] ⚠ Initialisation error: {e}")
        return None


# ── Public functions ─────────────────────────────────────────

def save_message(session_id: str, role: str, message: str) -> bool:
    """
    Save a single chat message to Firestore.

    Collection structure:
        chat_logs/
            {session_id}/          ← document per session
                messages/          ← subcollection
                    {auto-id}      ← one doc per message
                        role:      "user" | "bot"
                        message:   str
                        timestamp: datetime
    """
    db = _get_db()
    if db is None:
        return False  # Firebase not available; fail silently

    try:
        doc_ref = (
            db.collection("chat_logs")
              .document(session_id)
              .collection("messages")
              .document()           # auto-generated ID
        )
        doc_ref.set({
            "role":      role,
            "message":   message,
            "timestamp": datetime.now(timezone.utc)
        })
        return True

    except Exception as e:
        print(f"[Firebase] ⚠ save_message error: {e}")
        return False


def get_chat_history(session_id: str) -> list:
    """
    Retrieve all messages for a session, ordered by timestamp.
    Returns a list of dicts: [{ role, message, timestamp }, ...]
    """
    db = _get_db()
    if db is None:
        return []

    try:
        msgs_ref = (
            db.collection("chat_logs")
              .document(session_id)
              .collection("messages")
              .order_by("timestamp")
        )
        docs = msgs_ref.stream()

        result = []
        for doc in docs:
            d = doc.to_dict()
            result.append({
                "role":      d.get("role", "unknown"),
                "message":   d.get("message", ""),
                "timestamp": d.get("timestamp").isoformat() if d.get("timestamp") else None
            })
        return result

    except Exception as e:
        print(f"[Firebase] ⚠ get_chat_history error: {e}")
        return []
