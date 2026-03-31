# ============================================================
#  chatbot_logic.py — OpenRouter API with conversation memory
# ============================================================
import os, requests
from dotenv import load_dotenv
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
MODEL              = "openrouter/auto"   # auto picks best free model

SYSTEM_PROMPT = (
    "You are NexusAI, an advanced cloud-intelligent assistant "
    "built as a college cloud computing mini-project. "
    "You are helpful, concise, and technically accurate. "
    "You specialise in cloud computing, AI, and software development "
    "but can assist with any topic. "
    "If the user sends a message in a non-English language, reply in that same language."
)

def get_response(user_message: str, memory: list = None) -> str:
    if not OPENROUTER_API_KEY:
        return "⚠ OpenRouter API key not set. Add OPENROUTER_API_KEY to your .env file."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "http://localhost:5000",
        "X-Title":       "NexusAI Cloud Chatbot",
    }

    # Build messages: system + last 5 memory turns + current message
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if memory:
        messages += memory[-10:]   # last 10 turns (5 exchanges)
    messages.append({"role": "user", "content": user_message})

    payload = {"model": MODEL, "messages": messages, "max_tokens": 1024, "temperature": 0.7}

    try:
        res = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        try:
            data = res.json()
        except Exception:
            return f"⚠ Non-JSON response (HTTP {res.status_code}): {res.text[:200]}"

        print(f"\n[OpenRouter] status={res.status_code} | model={MODEL}")
        print(data)

        if "error" in data:
            code = data["error"].get("code", res.status_code)
            msg  = data["error"].get("message", "Unknown error")
            codes = {401:"⚠ Invalid API key.",402:"⚠ No credits.",403:"⚠ Access forbidden.",
                     404:"⚠ Model not found.",429:"⚠ Rate limited — wait 30s.",503:"⚠ Model overloaded."}
            return codes.get(int(code) if str(code).isdigit() else 0, f"⚠ API error {code}: {msg}")

        choices = data.get("choices")
        if not choices:
            return f"⚠ No choices in response: {data}"
        content = choices[0].get("message", {}).get("content", "").strip()
        return content if content else "⚠ AI returned an empty response."

    except requests.exceptions.Timeout:
        return "⚠ Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "⚠ Cannot reach OpenRouter. Check your internet."
    except Exception as e:
        return f"⚠ Unexpected error: {e}"
