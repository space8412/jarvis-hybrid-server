from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import traceback
import json
import requests
import tempfile
from datetime import datetime
from dateutil import tz

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


def classify_category(text):
    category_keywords = {
        "회의": ["회의", "미팅", "줌", "온라인회의", "컨퍼런스", "팀"],
        "상담": ["상담", "컨설팅", "문의", "점검", "전화상담", "방문상담"],
        "시공": ["시공", "설치", "공사", "작업", "철거", "시공회의"],
        "현장방문": ["방문", "현장", "측량", "실측", "현장확인", "공정확인"],
        "내부업무": ["테스트", "점검", "확인", "내부회의", "회의실예약"]
    }
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return category
    return "미정"


@app.get("/")
def root():
    return {"message": "Jarvis server is running."}


def build_prompt(text: str) -> str:
    today = datetime.now(tz=tz.gettz("Asia/Seoul")).strftime("%Y-%m-%d")
    return f"""오늘 날짜는 {today}야.
다음 명령어를 분석해서 intent, title, date, category를 JSON으로 반환해줘.

💡 아래 조건을 지켜서 분석해줘:
- intent는 register_schedule, delete_schedule, update_schedule 중 하나로 지정해줘.
- title은 장소나 일정의 키워드를 사용해줘. (예: '성수동', '사무실')
- date는 ISO 8601 형식으로 변환해줘.
- category는 시공, 미팅, 상담, 공사, 회의 등으로 지정해줘.
- 사용자가 시간 없이 날짜만 말한 경우, 해당 날짜를 종일 일정으로 처리해줘.
- "오늘", "내일" 같은 표현은 오늘 날짜 {today} 기준으로 계산해줘.

예시: '5월 2일 오후 3시에 성수동 시공 등록해줘' →
{{
  "intent": "register_schedule",
  "title": "성수동",
  "date": "2025-05-02T15:00:00",
  "category": "시공"
}}

예시: '5월 3일 성수동 미팅 삭제해줘' →
{{
  "intent": "delete_schedule",
  "title": "성수동",
  "date": "2025-05-03",
  "category": "미팅"
}}

지금 명령어: {text}
"""


def apply_time_correction(text, result):
    try:
        if "오후" in text and "T" in result.get("date", ""):
            hour_str = result["date"].split("T")[1][:2]
            if hour_str.isdigit() and int(hour_str) < 12:
                fixed_hour = int(hour_str) + 12
                result["date"] = result["date"].replace(f"T{hour_str}", f"T{fixed_hour:02d}")

        if "T00:00:00" in result.get("date", "") and "오전" not in text:
            result["date"] = result["date"].replace("T00:00:00", "T15:00:00")
    except:
        pass
    return result


def send_to_n8n(result):
    webhook_url = "https://n8n-server-lvqr.onrender.com/webhook/telegram-webhook"
    requests.post(webhook_url, json=result)


@app.post("/agent")
async def agent(request: Request):
    try:
        data = await request.json()
        text = data.get("text", "")
        if not text:
            return {"error": "text 필드가 비어있습니다."}

        prompt = build_prompt(text)

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
        result = apply_time_correction(text, result)
        result["category"] = classify_category(text)

        send_to_n8n(result)
        return result

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

        prompt = build_prompt(text)

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
        result = apply_time_correction(text, result)
        result["category"] = classify_category(text)

        send_to_n8n(result)
        return result

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
