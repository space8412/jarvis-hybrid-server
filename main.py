from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import traceback
import json
import requests
import tempfile

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 키
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

@app.get("/")
def root():
    return {"message": "Jarvis server is running."}

@app.post("/agent")
async def agent(request: Request):
    try:
        data = await request.json()
        text = data.get("text", "")
        if not text:
            return {"error": "text 필드가 비어있습니다."}

        prompt = f"""다음 명령어를 분석해서 일정 등록을 위한 title, date, category를 JSON으로 반환해줘:
예시: '5월 2일 오후 3시에 성수동 시공 등록해줘' →
{{
  "title": "성수동",
  "date": "2025-05-02T15:00:00",
  "category": "시공"
}}
지금 명령어: {text}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 한국어 명령어를 구조화하는 비서야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        payload = {"body": {"intent": "register_schedule", **result}}
        webhook_url = "https://themood.app.n8n.cloud/webhook/telegram-webhook"
        n8n_response = requests.post(webhook_url, json=payload)

        return payload

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

@app.post("/trigger")
async def trigger(request: Request):
    try:
        data = await request.json()
        message = data.get("message", {})
        text = ""

        if "voice" in message:
            file_id = message["voice"]["file_id"]
            file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            response = requests.get(file_url)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            text = transcript.strip()

        else:
            text = message.get("text", "")

        if not text:
            return {"error": "text가 비어 있습니다."}

        prompt = f"""다음 명령어를 분석해서 일정 등록을 위한 title, date, category를 JSON으로 반환해줘:
예시: '5월 2일 오후 3시에 성수동 시공 등록해줘' →
{{
  "title": "성수동",
  "date": "2025-05-02T15:00:00",
  "category": "시공"
}}
지금 명령어: {text}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 한국어 명령어를 구조화하는 비서야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        payload = {"body": {"intent": "register_schedule", **result}}
        webhook_url = "https://themood.app.n8n.cloud/webhook/telegram-webhook"
        n8n_response = requests.post(webhook_url, json=payload)

        return payload

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
