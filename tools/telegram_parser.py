from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils import get_logger

logger = get_logger(__name__)

class TelegramParser:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.app = None

    async def start(self):
        """Start the Telegram bot"""
        try:
            self.app = Application.builder().token(self.token).build()
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Start the bot
            await self.app.initialize()
            await self.app.start()
            await self.app.run_polling()
            
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {str(e)}")
            raise

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        try:
            await update.message.reply_text(
                "안녕하세요! 저는 당신의 개인 비서입니다. "
                "메시지를 보내시면 제가 도와드리겠습니다."
            )
        except Exception as e:
            logger.error(f"Error in start command: {str(e)}")
            raise

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            message = update.message.text
            user_id = update.effective_user.id
            
            # Log the message
            logger.info(f"Received message from user {user_id}: {message}")
            
            # Process the message (implement your logic here)
            response = f"메시지를 받았습니다: {message}"
            
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            raise

    async def send_message(self, message: str):
        """Send a message to the specified chat"""
        try:
            if not self.app:
                raise RuntimeError("Telegram bot not initialized")
                
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
            logger.info(f"Sent message to chat {self.chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise

    async def stop(self):
        """Stop the Telegram bot"""
        try:
            if self.app:
                await self.app.stop()
                await self.app.shutdown()
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {str(e)}")
            raise 