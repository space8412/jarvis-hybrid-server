from fastapi import FastAPI, Request
from tools.telegram_parser import extract_text_from_telegram
from tools.gpt_parser import parse_command
from tools.calendar import correct_datetime_format
from tools.classifier import classify_category
from tools.notion_writer import save_to_notion, delete_from_notion, update_notion_page

app = FastAPI()

@app.post("/trigger")
async def trigger(request: Request):
    try:
        # 📥 텔레그램 메시지 수신
        data = await request.json()
        print("📥 받은 데이터:", data)  # 디버깅용 출력

        # 🗣️ 텍스트 또는 음성 → 텍스트 변환
        text = extract_text_from_telegram(data)
        print("🎤 추출된 텍스트:", text)  # 디버깅용 출력
        if not text:
            return {"error": "text가 비어 있습니다."}

        # 🧠 명령어 분석 (GPT 기반 파싱)
        parsed = parse_command(text)
        print("🧠 파싱 결과:", parsed)  # 디버깅용 출력

        # ⏰ 시간 포맷 보정 (오전/오후 등)
        parsed = correct_datetime_format(text, parsed)

        # 🏷️ 일정 카테고리 자동 분류
        parsed["category"] = classify_category(text)

        # 📌 intent에 따라 실행 분기
        if parsed.get("intent") == "register_schedule":
            notion_result = save_to_notion(parsed)
            print("📌 Notion 등록 결과:", notion_result)
            return {"status": "ok", "intent": "register_schedule", "notion": notion_result}

        elif parsed.get("intent") == "delete_schedule":
            notion_result = delete_from_notion(parsed)
            print("📌 Notion 삭제 결과:", notion_result)
            return {"status": "ok", "intent": "delete_schedule", "notion": notion_result}

        elif parsed.get("intent") == "update_schedule":
            notion_result = update_notion_page(parsed)
            print("📌 Notion 수정 결과:", notion_result)
            return {"status": "ok", "intent": "update_schedule", "notion": notion_result}

        # 지원되지 않는 intent 처리
        return {"error": f"지원되지 않는 intent: {parsed.get('intent')}"}

    except Exception as e:
        import traceback
        print("🚨 예외 발생:", str(e))
        return {"error": str(e), "trace": traceback.format_exc()}
