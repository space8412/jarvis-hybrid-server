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
        data = await request.json()
        text = extract_text_from_telegram(data)
        if not text:
            return {"error": "text가 비어 있습니다."}

        parsed = parse_command(text)
        parsed = correct_datetime_format(text, parsed)
        parsed["category"] = classify_category(text)

        if parsed.get("intent") == "register_schedule":
            notion_result = save_to_notion(parsed)
            return {
                "status": "ok",
                "intent": "register_schedule",
                "notion": notion_result
            }

        elif parsed.get("intent") == "delete_schedule":
            notion_result = delete_from_notion(parsed)
            return {
                "status": "ok",
                "intent": "delete_schedule",
                "notion": notion_result
            }

        elif parsed.get("intent") == "update_schedule":
            notion_result = update_notion_page(parsed)
            return {
                "status": "ok",
                "intent": "update_schedule",
                "notion": notion_result
            }

        return {"error": f"지원되지 않는 intent: {parsed.get('intent')}"}

    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}
