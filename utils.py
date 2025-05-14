import logging
from config import LOG_LEVEL, LOG_FILE
import os

def setup_logging():
    """Configure logging settings"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

def get_logger(name):
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)

def format_error_message(error):
    """Format error message for logging"""
    return f"Error: {str(error)}"

def validate_required_env_vars():
    """Validate that all required environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID',
        'NOTION_API_KEY',
        'NOTION_DATABASE_ID'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}") 