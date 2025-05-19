import os
import logging
from typing import Union, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from tools.telegram_parser import setup_telegram_app
from tools.clarify import clarify_command
from tools.calendar_register import register_schedule
from tools.calendar_update import update_schedule
from tools.calendar_delete import delete_schedule
from tools.notion_writer import (
    save_to_notion,
    delete_from_notion,
    update_notion_schedule
)

# ✅ .env 환경변수 로드
load_dotenv()

# ✅ 로그 레벨 설정
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

@app.post("/trigger")
async def trigger(request: Request):
    try:
        body = await request.json()
        msg_obj = body.get("message", {})
        message_text = msg_obj.get("text", "")

        logger.info(f"[trigger] 수신된 메시지: {message_text}")
        parsed = clarify_command(message_text)
        logger.debug(f"[trigger] clarify 결과: {parsed}")

        intent = parsed.get("intent", "")
        title = parsed.get("title", "")
        start_date = parsed.get("start_date", "")
        category = parsed.get("category", "")
        origin_title = parsed.get("origin_title", "")
        origin_date = parsed.get("origin_date", "")

        notion_result = None
        calendar_result = None

        if intent == "register_schedule":
            try:
                register_schedule(title, start_date, category)
                calendar_result = "✅ Google Calendar 등록 완료"
            except Exception as e:
                calendar_result = f"❌ 캘린더 등록 실패: {e}"

            try:
                notion_result = save_to_notion(parsed)
            except Exception as e:
                notion_result = f"❌ Notion 등록 실패: {e}"

        elif intent == "update_schedule":
            try:
                update_schedule(origin_title, origin_date, start_date, category)
                calendar_result = "✅ Google Calendar 수정 완료"
            except Exception as e:
                calendar_result = f"❌ 캘린더 수정 실패: {e}"

            try:
                notion_result = update_notion_schedule({
                    "title": title,
                    "start_date": start_date,
                    "category": category,
                    "origin_title": origin_title,
                    "origin_date": origin_date
                })
            except Exception as e:
                notion_result = f"❌ Notion 수정 실패: {e}"

        elif intent == "delete_schedule":
            try:
                calendar_result = delete_schedule(title, start_date, category)
            except Exception as e:
                calendar_result = f"❌ 캘린더 삭제 실패: {e}"

            try:
                notion_result = delete_from_notion({
                    "title": title,
                    "start_date": start_date,
                    "category": category
                })
            except Exception as e:
                notion_result = f"❌ Notion 삭제 실패: {e}"

        else:
            return {"status": "ignored", "message": "처리 가능한 명령이 아닙니다."}

        return {
            "status": "success",
            "calendar": calendar_result,
            "notion": notion_result
        }

    except Exception as e:
        logger.error(f"[trigger] 오류 발생: {str(e)}")
        return JSONResponse(status_code=200, content={
            "status": "error",
            "message": str(e)
        })

@app.post("/clarify")
async def clarify_test(request: Request):
    try:
        body = await request.json()
        message_text = body.get("message", "")
        parsed = clarify_command(message_text)
        return parsed

    except Exception as e:
        logger.error(f"[clarify] 테스트 오류 발생: {str(e)}")
        return JSONResponse(status_code=500, content={"detail": str(e)})
