import os
import json
import logging
import traceback
import requests
from typing import Union, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import OpenAI
from tempfile import NamedTemporaryFile

from tools.clarify import clarify_command
from tools.calendar_register import register_schedule
from tools.calendar_update import update_schedule
from tools.calendar_delete import delete_schedule
from tools.notion_writer import (
    save_to_notion,
    delete_from_notion
)
from tools.update_notion_schedule import update_notion_schedule  # ✅ 수정된 import

# ✅ 환경변수 로드 및 설정
load_dotenv()
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "NOTION_TOKEN", "NOTION_DATABASE_ID"]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise RuntimeError(f"❌ 환경변수 {var}가 설정되지 않았습니다.")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ FastAPI 앱 초기화
app = FastAPI()

# ✅ intent 분기 처리
@app.post("/trigger")
async def trigger(request: Request):
    try:
        body = await request.json()
        msg_obj = body.get("message", {})
        message_text = ""

        # ✅ 음성 메시지 처리
        if "voice" in msg_obj:
            file_id = msg_obj["voice"]["file_id"]
            file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            voice_data = requests.get(file_url).content

            with NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
                tmp_file.write(voice_data)
                tmp_path = tmp_file.name

            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                message_text = transcript.strip()
        else:
            message_text = msg_obj.get("text", "")

        if not message_text:
            logger.warning("[trigger] 입력된 메시지가 비어 있습니다.")
            return {"status": "error", "message": "입력된 메시지가 없습니다."}

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
                notion_result = update_notion_schedule(parsed)
            except Exception as e:
                notion_result = f"❌ Notion 수정 실패: {e}"

        elif intent == "delete_schedule":
            try:
                calendar_result = delete_schedule(title, start_date, category)
            except Exception as e:
                calendar_result = f"❌ 캘린더 삭제 실패: {e}"

            try:
                notion_result = delete_from_notion(parsed)
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

# ✅ 명령어 파싱 테스트용
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

# ✅ GPT 기반 명령어 구조화 (릴스, 블로그 등 확장 가능)
@app.post("/agent")
async def agent(request: Request):
    try:
        body = await request.json()
        text = body.get("text", "")

        if not text:
            return {"error": "text 필드가 비어 있습니다."}

        today = datetime.now().strftime("%Y-%m-%d")
        prompt = f"""오늘 날짜는 {today}야.
명령어를 분석해서 intent, title, start_date, origin_date, category, origin_title 값을 아래 형식의 JSON으로 반환해줘.

📌 intent 값은 아래 중 하나로만:
- "register_schedule"
- "update_schedule"
- "delete_schedule"

📌 category 값은 반드시 아래 중 하나로 한글로만 써줘:
- 회의
- 상담
- 시공
- 공사
- 콘텐츠
- 개인
- 현장방문
- 기타

명령어: {text}

형식:
{{
  "title": "...",
  "start_date": "...",
  "origin_date": "...",
  "intent": "...",
  "category": "...",
  "origin_title": "..."
}}"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0
        )

        parsed = json.loads(response.choices[0].message.content.strip())
        return parsed

    except Exception as e:
        logger.error(f"[agent] 오류 발생: {str(e)}")
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "trace": traceback.format_exc()
        })
