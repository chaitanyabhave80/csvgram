import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

MAX_COLUMNS = 50
MAX_ROWS = 5000
MAX_COLUMN_NAME_LENGTH = 100
MAX_CELL_LENGTH = 5000
MISSING_VALUE = "N/A"
