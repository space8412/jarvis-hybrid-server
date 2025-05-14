import asyncio
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from tools.telegram_parser import TelegramParser
from tools.gpt_parser import GPTParser
from tools.notion_writer import NotionWriter
from tools.calendar import CalendarManager
from tools.classifier import MessageClassifier
from tools.clarify import MessageClarifier
from tools.verify_database import DatabaseVerifier
from utils import setup_logging, validate_required_env_vars, get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(title="Jarvis Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JarvisServer:
    def __init__(self):
        self.telegram = TelegramParser()
        self.gpt = GPTParser()
        self.notion = NotionWriter()
        self.calendar = CalendarManager()
        self.classifier = MessageClassifier()
        self.clarifier = MessageClarifier()

    async def process_message(self, message: str, user_id: str):
        """Process incoming messages"""
        try:
            # First, clarify the message
            clarification = self.clarifier.clarify_message(message)
            
            # If the message is ambiguous, ask for clarification
            if not clarification.get('task_name') or not clarification.get('start_time'):
                questions = self.clarifier.get_clarification_questions(message)
                return f"메시지를 더 명확하게 이해하기 위해 몇 가지 질문을 드리겠습니다:\n{questions}"

            # Get the intent from the clarified message
            intent = self.classifier.classify(message)["intent"]

            # Handle different intents
            if intent == "task":
                # Create a task in Notion
                self.notion.create_page(
                    title=clarification['task_name'],
                    content=message,
                    tags=["task"]
                )
                response = "할일이 Notion에 추가되었습니다."

            elif intent == "schedule":
                # Create a calendar event
                if clarification.get('start_time') and clarification.get('end_time'):
                    self.calendar.create_event(
                        summary=clarification['task_name'],
                        start_time=clarification['start_time'],
                        end_time=clarification['end_time']
                    )
                    response = "일정이 캘린더에 추가되었습니다."
                else:
                    response = "일정의 시작 시간과 종료 시간을 알려주세요."

            elif intent == "reminder":
                # Create a reminder in Notion
                self.notion.create_page(
                    title=clarification['task_name'],
                    content=message,
                    tags=["reminder"]
                )
                response = "알림이 설정되었습니다."

            else:
                # For other intents, use GPT's response
                response = self.gpt.parse_message(message)

            return response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "죄송합니다. 메시지 처리 중 오류가 발생했습니다."

    async def start(self):
        """Start the Jarvis server"""
        try:
            # Validate environment variables
            validate_required_env_vars()

            # Setup logging
            setup_logging()

            # Verify and fix database structure
            verifier = DatabaseVerifier()
            if not verifier.verify_and_fix_database():
                logger.error("Failed to verify/fix database structure")
                return

            # Start the Telegram bot
            await self.telegram.start()

        except Exception as e:
            logger.error(f"Error starting Jarvis server: {str(e)}")
            raise

    async def stop(self):
        """Stop the Jarvis server"""
        try:
            await self.telegram.stop()
        except Exception as e:
            logger.error(f"Error stopping Jarvis server: {str(e)}")
            raise

# Create Jarvis instance
jarvis = JarvisServer()

# FastAPI routes
@app.get("/")
async def root():
    return {"status": "Jarvis server is running"}

@app.post("/process")
async def process_message(message: str, user_id: str):
    try:
        response = await jarvis.process_message(message, user_id)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    await jarvis.start()

@app.on_event("shutdown")
async def shutdown_event():
    await jarvis.stop()

if __name__ == "__main__":
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000) 