from pathlib import Path
import os

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("FASHION_IMAGE_DB_PATH", BASE_DIR / "app.db"))
UPLOAD_DIR = Path(os.getenv("FASHION_IMAGE_UPLOAD_DIR", BASE_DIR / "data" / "uploads"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("FASHION_IMAGE_MODEL", "gpt-4.1-mini")
