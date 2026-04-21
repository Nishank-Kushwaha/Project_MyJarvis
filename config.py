import os
import dotenv

dotenv.load_dotenv()

# ── API keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY   = os.getenv("NEWS_API_KEY")

# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_MODEL         = "gemini-2.0-flash"
GEMINI_SYSTEM_PROMPT = (
    "You are Jarvis, a smart AI assistant like Alexa. Keep answers short and spoken-friendly."
)

# ── URLs ──────────────────────────────────────────────────────────────────────
WEBSITES = {
    "google":    "https://google.com",
    "youtube":   "https://youtube.com",
    "facebook":  "https://facebook.com",
    "linkedin":  "https://linkedin.com",
    "instagram": "https://instagram.com",
}

NEWS_URL = "https://newsdata.io/api/1/latest"

# ── Filesystem ────────────────────────────────────────────────────────────────
SCREENSHOT_DIR = "Screenshots"

# ── Wake word ─────────────────────────────────────────────────────────────────
WAKE_WORD = "jarvis"