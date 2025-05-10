from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import traceback
import json
import requests
import tempfile
from datetime import datetime, timedelta, date
from dateutil import tz
from dateutil.parser import isoparse
from tools.clarify import clarify_schedule_update

app = FastAPI()

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 환경변수 체크
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN 환경변수가 설정되지 않았습니다.")

client = OpenAI(api_key=OPENAI_API_KEY)

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

def get_next_week_dates():
    today = date.today()
    next_monday = today + timedelta(days=-today.weekday() + 7)
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    return {
        weekdays[i]: (next_monday + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(7)
    }

def build_prompt(text: str) -> str:
    today = datetime.now(tz=tz.gettz("Asia/Seoul")).strftime("%Y-%m-%d")
    is_update = "수정" in text or "변경" in text or "바꿔" in text
    weekmap = get_next_week_dates()
    weekinfo = "\n".join([f"- 다음주 {k}: {v}" for k, v in weekmap.items()])

    if is_update:
        return f"""오늘 날짜는 {today}야.
{weekinfo}
이 정보를 기준으로 날짜를 정확히 계산해줘.
다음 명령어는 일정을 수정하려는 요청이야. 아래 항목을 JSON 형식으로 분석해줘:
- intent: 항상 "update_schedule"
- origin_title: 수정 전 일정 제목
- origin_date: 수정 전 일정 시간 (ISO 8601)
- title: 새로운 일정 제목 (같으면 그대로)
- date: 새로운 일정 시간 (ISO 8601)
- category: 회의, 상담, 현장방문 등으로 분류
지금 명령어: {text}
JSON만 출력해줘.
"""
    else:
        return f"""오늘 날짜는 {today}야.
{weekinfo}
이 정보를 기준으로 날짜를 정확히 계산해줘.
다음 명령어를 분석해서 intent, title, date, category를 JSON으로 반환해줘.
💡 아래 조건을 지켜서 분석해줘:
- intent는 register_schedule, delete_schedule, update_schedule 중 하나로 지정해줘.
- title은 장소나 일정의 키워드를 사용해줘. (예: '성수동', '사무실')
- date는 ISO 8601 형식으로 변환해줘.
- category는 시공, 미팅, 상담, 공사, 회의 등으로 지정해줘.
- 사용자가 시간 없이 날짜만 말한 경우, 해당 날짜를 종일 일정으로 처리해줘.
- "오늘", "내일" 같은 표현은 오늘 날짜 {today} 기준으로 계산해줘.
- **과거 날짜라도 그대로 사용해줘. 현재 날짜를 기준으로 미래로 바꾸지 마.**
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
        if result.get("origin_date") and "T00:00:00" in result["origin_date"] and "오전" not in text:
            result["origin_date"] = result["origin_date"].replace("T00:00:00", "T15:00:00")
    except:
        pass
    return result

def parse_and_send(text: str):
    prompt = build_prompt(text)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 한국어 명령어를 구조화하는 비서야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    if not response.choices:
        return {"error": "GPT 응답이 없습니다."}
    content = response.choices[0].message.content
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {"error": "GPT 응답이 JSON 형식이 아닙니다.", "raw": content}
    result = apply_time_correction(text, result)
    result["category"] = classify_category(text)
    if "origin_date" not in result or not result["origin_date"]:
        result["origin_date"] = result.get("date", "")
    if "origin_title" not in result or not result["origin_title"]:
        result["origin_title"] = result.get("title", "")
    if result.get("date"):
        dt = isoparse(result["date"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz.gettz("Asia/Seoul"))
        result["date"] = dt.isoformat()
        start = dt.astimezone(tz.gettz("Asia/Seoul"))
        result["start"] = start.isoformat()
        result["end"] = (start + timedelta(hours=1)).isoformat()
    if result.get("origin_date"):
        odt = isoparse(result["origin_date"])
        if odt.tzinfo is None:
            odt = odt.replace(tzinfo=tz.gettz("Asia/Seoul"))
        result["origin_date"] = odt.isoformat()
    webhook_url = "https://n8n-server-lvqr.onrender.com/webhook/telegram-webhook"
    print("📤 전송 데이터:", json.dumps(result, ensure_ascii=False, indent=2))
    print("🔗 전송 대상 URL:", webhook_url)
    n8n_response = requests.post(webhook_url, json=result)
    print("📡 n8n 응답 상태:", n8n_response.status_code)
    print("📨 n8n 응답 내용:", n8n_response.text)
    return result

@app.post("/agent")
async def agent(request: Request):
    try:
        data = await request.json()
        text = data.get("text", "")
        if not text:
            return {"error": "text 필드가 비어있습니다."}
        return parse_and_send(text)
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
            text = data.get("text", "")
        if not text:
            return {"error": "text가 비어 있습니다."}
        return parse_and_send(text)
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

@app.post("/clarify")
async def clarify(request: Request):
    try:
        data = await request.json()
        text = data.get("text", "")
        if not text:
            return {"error": "text 필드가 비어 있습니다."}
        return clarify_schedule_update(text)
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}
