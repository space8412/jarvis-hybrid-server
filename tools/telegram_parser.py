import os
from telegram.ext import Application

def setup_telegram_app() -> Application:
    """
    Telegram 애플리케이션을 초기화하고 반환합니다.
    
    :return: Telegram Application 객체
    """  
    telegram_token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(telegram_token).build()
    return app