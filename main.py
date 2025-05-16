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
    save_to_notion,              # ✅ 수정된 import
    delete_from_notion,
    update_notion_schedule
)

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
        msg_obj = body.get("message", {})
        message_text = msg_obj.get("text", "")

        logger.info(f"[trigger] 수신된 메시지: {message_text}")

        # ⬇️ 명령 파싱 (단 1회만 실행)
        parsed = clarify_command(message_text)
        logger.debug(f"[trigger] clarify 결과: {parsed}")

        intent = parsed.get("intent", "")
        title = parsed.get("title", "")
        start_date = parsed.get("start_date", "")
        category = parsed.get("category", "")
        origin_title = parsed.get("origin_title", "")
        origin_date = parsed.get("origin_date", "")

        # ⬇️ intent 기반 분기 처리
        if intent == "register_schedule":
            register_schedule(title, start_date, category)
            save_to_notion(parsed)  # ✅ 수정된 함수명 및 인자
            return {"status": "success", "message": f"{start_date} 일정 등록 완료"}

        elif intent == "update_schedule":
            update_schedule(
                origin_title=origin_title,
                origin_date=origin_date,
                new_date=start_date,
                category=category
            )
            update_notion_schedule(
                origin_title=origin_title,
                origin_date=origin_date,
                new_date=start_date,
                category=category
            )
            return {"status": "success", "message": f"{origin_date} → {start_date} 일정 수정 완료"}

        elif intent == "delete_schedule":
            delete_result = delete_schedule(title, start_date, category)
            notion_result = delete_from_notion(title, start_date, category)
            return {"status": "success", "message": f"{delete_result} / {notion_result}"}

        else:
            return {"status": "ignored", "message": "처리 가능한 명령이 아닙니다."}

    except Exception as e:
        logger.error(f"[trigger] 오류 발생: {str(e)}")
        return JSONResponse(status_code=200, content={
            "status": "error",
            "message": str(e)
        })


# ✅ clarify 단독 테스트용 엔드포인트
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
