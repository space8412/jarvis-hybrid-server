import os
from typing import Union
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from tools.telegram_parser import setup_telegram_app
from tools.clarify import clarify_command
from tools.calendar_register import register_schedule
from tools.calendar_delete import delete_schedule

load_dotenv()
app = FastAPI()
telegram_app = setup_telegram_app()

@app.post("/trigger")
async def trigger_command(request: Request):
    data = await request.json()
    message = data["message"]
    
    title, start_date, category, intent = clarify_command(message)
    
    if intent == "register_schedule":
        register_schedule(title, start_date, category)
    elif intent == "delete_schedule":
        delete_schedule(start_date)
    else:
        print(f"Unknown intent: {intent}")

@app.post("/webhook")
async def handle_telegram_update(request: Request):
    data = await request.json()
    update = telegram_app.parse_update(data)
    
    if update.message:
        message_text = update.message.text
        title, start_date, category, intent = clarify_command(message_text)
        
        if intent == "register_schedule":
            register_schedule(title, start_date, category)
            await update.message.reply_text(f"일정이 등록되었습니다: {title} ({start_date})")
        elif intent == "delete_schedule":
            delete_schedule(start_date)
            await update.message.reply_text(f"{start_date} 일정이 삭제되었습니다.")
        else:
            await update.message.reply_text("죄송합니다. 요청을 이해하지 못했습니다.")

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)