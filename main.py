import os
import logging
from typing import Union, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

from tools.telegram_parser import setup_telegram_app
from tools.clarify import clarify_command
from tools.calendar_register import register_schedule
from tools.calendar_delete import delete_schedule
from tools.verify_database import verify_environment

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('jarvis.log')
    ]
)
logger = logging.getLogger(__name__)

# 환경변수 로드 및 검증
load_dotenv()
if not verify_environment():
    logger.error("필수 환경변수가 누락되었습니다. 서버를 종료합니다.")
    exit(1)

app = FastAPI()
telegram_app = setup_telegram_app()

async def process_intent(title: str, start_date: str, category: str, intent: str) -> Dict[str, Any]:
    """
    intent에 따른 일정 처리를 수행하는 공통 함수
    
    :return: 처리 결과 메시지
    """
    try:
        if intent == "register_schedule":
            register_schedule(title, start_date, category)
            return {"status": "success", "message": f"일정이 등록되었습니다: {title} ({start_date})"}
        elif intent == "delete_schedule":
            delete_schedule(start_date)
            return {"status": "success", "message": f"{start_date} 일정이 삭제되었습니다."}
        else:
            return {"status": "error", "message": "죄송합니다. 요청을 이해하지 못했습니다."}
    except Exception as e:
        logger.error(f"일정 처리 중 오류 발생: {str(e)}")
        return {"status": "error", "message": "일정 처리 중 오류가 발생했습니다."}

@app.post("/trigger")
async def trigger_command(request: Request):
    try:
        data = await request.json()
        message = data["message"]
        
        title, start_date, category, intent = clarify_command(message)
        result = await process_intent(title, start_date, category, intent)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except Exception as e:
        logger.error(f"Trigger 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")

@app.post("/webhook")
async def handle_telegram_update(request: Request):
    try:
        data = await request.json()
        update = telegram_app.parse_update(data)
        
        if update.message:
            message_text = update.message.text
            title, start_date, category, intent = clarify_command(message_text)
            
            result = await process_intent(title, start_date, category, intent)
            await update.message.reply_text(result["message"])
    except Exception as e:
        logger.error(f"Webhook 처리 중 오류 발생: {str(e)}")
        if update.message:
            await update.message.reply_text("처리 중 오류가 발생했습니다.")

@app.get("/")
def read_root():
    return {"status": "running", "service": "Jarvis Automation Server"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Jarvis Automation Server 시작")
    uvicorn.run(app, host="0.0.0.0", port=8000)