from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import traceback
import json
import requests
import tempfile
from datetime import datetime

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

        today = datetime.now().strftime("%Y-%m-%d")

        prompt = f"""오늘 날짜는 {today}야.
다음 명령어를 분석해서 일정 등록을 위한 title, date, category를 JSON으로 반환해줘.

💡 아래 조건을 지켜서 분석해줘:
- 논현동, 성수동, 합정동, 한남동, 청담동, 압구정동 등 실제 존재하는 서울 지역 지명을 기준으로 오타가 있으면 보정해줘.
- 날짜와 시간도 한국어 표현(예: '오후 2시', '5월 10일', '오늘 오후 3시')을 정확히 ISO 형식으로 변환해줘. 현재 날짜는 기준 날짜로 사용해.
- '오늘', '내일', '모레' 같은 상대 날짜는 현재 날짜를 기준으로 변환해줘.
- '오전', '오후'는 24시간제로 변환해줘. 예: '오후 5시' → 17:00
- '사무실', '논현동' 같은 장소 표현은 그대로 title로 사용해줘.
- '회의', '미팅', '현장미팅', '상담', '시공', '공사' 등은 category로 분류해줘.
- 사용자가 시간 없이 날짜만 말한 경우, 해당 날짜를 종일 일정으로 처리해줘.

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

        today = datetime.now().strftime("%Y-%m-%d")

        prompt = f"""오늘 날짜는 {today}야.
다음 명령어를 분석해서 일정 등록을 위한 title, date, category를 JSON으로 반환해줘.

💡 아래 조건을 지켜서 분석해줘:
- 논현동, 성수동, 합정동, 한남동, 청담동, 압구정동 등 실제 존재하는 서울 지역 지명을 기준으로 오타가 있으면 보정해줘.
- 날짜와 시간도 한국어 표현(예: '오후 2시', '5월 10일', '오늘 오후 3시')을 정확히 ISO 형식으로 변환해줘. 현재 날짜는 기준 날짜로 사용해.
- '오늘', '내일', '모레' 같은 상대 날짜는 현재 날짜를 기준으로 변환해줘.
- '오전', '오후'는 24시간제로 변환해줘. 예: '오후 5시' → 17:00
- '사무실', '논현동' 같은 장소 표현은 그대로 title로 사용해줘.
- '회의', '미팅', '현장미팅', '상담', '시공', '공사' 등은 category로 분류해줘.
- 사용자가 시간 없이 날짜만 말한 경우, 해당 날짜를 종일 일정으로 처리해줘.

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
