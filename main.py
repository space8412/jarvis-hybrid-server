from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import traceback
import json
import requests

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API 키로 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 서버 상태 확인용
@app.get("/")
def root():
    return {"message": "Jarvis server is running."}

# 수동 분석용 (예: Postman에서 직접 text 보내는 경우)
@app.post("/agent")
async def agent(request: Request):
    try:
        data = await request.json()
        print("📥 요청 데이터:", data)

        text = data.get("text", "")
        if not text:
            return {"error": "text 필드가 비어있습니다."}

        # GPT 프롬프트 구성
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
        print("📦 GPT 응답 내용:", content)

        result = json.loads(content)

        # n8n Webhook으로 결과 전송
        webhook_url = "https://themood.app.n8n.cloud/webhook/telegram-webhook"
        n8n_response = requests.post(webhook_url, json=result)
        print("📨 n8n 전송 응답:", n8n_response.status_code, n8n_response.text)

        return result

    except Exception as e:
        print("❌ agent 오류:", traceback.format_exc())
        return {"error": str(e), "trace": traceback.format_exc()}

# 텔레그램 메시지를 수신하는 자동 트리거 경로
@app.post("/trigger")
async def trigger(request: Request):
    try:
        data = await request.json()
        message = data.get("message", {})
        text = message.get("text", "")

        if not text:
            return {"error": "텔레그램 메시지에 text가 없습니다."}

        print("🤖 텔레그램 메시지 수신:", text)

        # 분석 프롬프트 구성
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
        print("📦 GPT 응답 내용:", content)

        result = json.loads(content)

        # n8n Webhook으로 결과 전송
        webhook_url = "https://themood.app.n8n.cloud/webhook/telegram-webhook"
        n8n_response = requests.post(webhook_url, json=result)
        print("📨 n8n 전송 응답:", n8n_response.status_code, n8n_response.text)

        return result

    except Exception as e:
        print("❌ trigger 오류:", traceback.format_exc())
        return {"error": str(e), "trace": traceback.format_exc()}
