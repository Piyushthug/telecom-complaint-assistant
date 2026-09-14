import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
DATA_DIR = BASE_DIR / "data"
FAISS_INDEX_DIR = BASE_DIR / "backend" / "rag" / "index"
SQLITE_DB_PATH = DATA_DIR / "complaint_history.db"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

TOP_K = int(os.getenv("TOP_K", "3"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

CATEGORIES = [
    "INTERNET_OUTAGE",
    "SLOW_INTERNET",
    "BILLING",
    "REFUND",
    "CUSTOMER_SERVICE",
]

SENTIMENTS = [
    "POSITIVE",
    "NEUTRAL",
    "NEGATIVE",
    "VERY_NEGATIVE",
]

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))

REPEATED_CONTACT_THRESHOLD = int(os.getenv("REPEATED_CONTACT_THRESHOLD", "2"))
