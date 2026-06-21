import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env файла
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env file")

ADMIN_ID = 594991072