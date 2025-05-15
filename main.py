import os
import logging
from typing import Union, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

from tools.telegram_parser import setup_telegram_app
from tools.clarify import clarify_command
from tools.calendar_register import register_to_calendar
from tools.notion_writer import save_to_notion

# ✅ .env 환경변수 로드
load_dotenv()

# ✅ 로그 레벨 설정 (기본값 INFO)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# ✅ 필수 환경변수 확인
REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "NOTION_TOKEN", "NOTION_DATABASE_ID"]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise RuntimeError(f"❌ 환경변수 {var}가 설정되지 않았습니다.")

# ✅ FastAPI 앱 초기화
app = FastAPI()

# ✅ 텔레그램 명령 수신 엔드포인트
@app.post("/trigger")
async def trigger(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "")

        logger.info(f"[trigger] 수신된 메시지: {message}")

        # ⬇️ 명령 파싱
        title, start_date, category, intent = clarify_command(message)

        parsed = {
            "title": title,
            "start_date": start_date,
            "category": category,
            "intent": intent
        }

        logger.debug(f"[trigger] clarify 결과: {parsed}")

        # ⬇️ intent 기반 분기
        if intent == "register_schedule":
            cal_result = register_to_calendar(parsed)
            notion_result = save_to_notion(parsed)
            return {
                "status": "success",
                "calendar": cal_result,
                "notion": notion_result
            }

        elif intent == "delete_schedule":
            return {
                "status": "ready",
                "message": "삭제 기능은 추후 구현됩니다."
            }

        else:
            return {
                "status": "ignored",
                "message": "처리 가능한 명령이 아닙니다."
            }

    except Exception as e:
        logger.error(f"[trigger] 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ✅ clarify 단독 테스트용 엔드포인트
@app.post("/clarify")
async def clarify_test(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "")
        title, start_date, category, intent = clarify_command(message)

        return {
            "title": title,
            "start_date": start_date,
            "category": category,
            "intent": intent
        }

    except Exception as e:
        logger.error(f"[clarify] 테스트 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
