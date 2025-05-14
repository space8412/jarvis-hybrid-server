from fastapi import FastAPI, Request
from tools.telegram_parser import extract_text_from_telegram
from tools.gpt_parser import parse_command
from tools.calendar import correct_datetime_format
from tools.classifier import classify_category
from tools.clarify import clarify_intent
from tools.notion_writer import save_to_notion, delete_from_notion, update_notion_page

app = FastAPI()

@app.post("/trigger")
async def trigger(request: Request):
    try:
        # 📥 텔레그램 메시지 수신
        data = await request.json()
        print("📥 받은 데이터:", data)

        # 🗣️ 텍스트 추출
        text = extract_text_from_telegram(data)
        print("🎤 추출된 텍스트:", text)
        if not text:
            return {"error": "text가 비어 있습니다."}

        # 🧠 명령어 파싱
        parsed = parse_command(text)
        parsed = clarify_intent(parsed)  # ← intent 분기 확정 추가
        print("🧠 파싱 결과:", parsed)

        # ⏰ 시간 포맷 보정
        parsed = correct_datetime_format(text, parsed)

        # 🏷️ 카테고리 자동 분류
        parsed["category"] = classify_category(text)

        # ✅ intent 기반 실행 분기
        intent = parsed.get("intent")

        if intent == "register_schedule":
            result = save_to_notion(parsed)
        elif intent == "delete_schedule":
            result = delete_from_notion(parsed)
        elif intent == "update_schedule":
            result = update_notion_page(parsed)
        else:
            return {"error": f"지원되지 않는 intent: {intent}"}

        return {"status": "ok", "intent": intent, "notion": result}

    except Exception as e:
        import traceback
        print("🚨 예외 발생:", str(e))
        return {"error": str(e), "trace": traceback.format_exc()}
