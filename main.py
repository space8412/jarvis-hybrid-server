from fastapi import FastAPI, Request
import logging
from tools.telegram_parser import extract_text_from_telegram
from tools.gpt_parser import parse_command
from tools.calendar import correct_datetime_format
from tools.classifier import classify_category
from tools.clarify import clarify_intent
from tools.notion_writer import save_to_notion, delete_from_notion, update_notion_page
from utils import setup_logging, APIError, ValidationError

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/trigger")
async def trigger(request: Request):
    try:
        # 📥 텔레그램 메시지 수신
        data = await request.json()
        logger.info(f"Received data: {data}")

        # 🗣️ 텍스트 추출
        text = await extract_text_from_telegram(data)
        logger.info(f"Extracted text: {text}")
        
        if not text:
            raise ValidationError("Empty text")

        # 🧠 명령어 파싱
        parsed = parse_command(text)
        parsed = clarify_intent(parsed)
        logger.info(f"Parsed result: {parsed}")

        # ⏰ 시간 포맷 보정
        parsed = correct_datetime_format(text, parsed)

        # 🏷️ 카테고리 자동 분류
        parsed["category"] = classify_category(text)

        # ✅ intent 기반 실행 분기
        intent = parsed.get("intent")

        if intent == "register_schedule":
            result = await save_to_notion(parsed)
        elif intent == "delete_schedule":
            result = await delete_from_notion(parsed)
        elif intent == "update_schedule":
            result = await update_notion_page(parsed)
        else:
            raise ValidationError(f"Unsupported intent: {intent}")

        return {"status": "ok", "intent": intent, "notion": result}

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return {"error": str(e)}
    except APIError as e:
        logger.error(f"API error: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"error": "Internal server error"}
