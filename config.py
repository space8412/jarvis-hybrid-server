import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Notion Configuration
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

# Google Calendar Configuration
GOOGLE_CALENDAR_CREDENTIALS_FILE = os.getenv('GOOGLE_CALENDAR_CREDENTIALS_FILE')
GOOGLE_CALENDAR_TOKEN_FILE = os.getenv('GOOGLE_CALENDAR_TOKEN_FILE')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'jarvis.log') 