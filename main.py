from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import traceback
import json

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI 클라이언트 생성
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
def root():
    return {"message": "Jarvis server is running."}

@app.post("/agent")
async def agent(request: Request):
    try:
        data = await request.json()
        print("📥 요청 데이터:", data)

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
        print("📦 GPT 응답 내용:", content)

        result = json.loads(content)
        return result

    except Exception as e:
        print("❌ 오류 발생:", traceback.format_exc())
        return {"error": str(e), "trace": traceback.format_exc()}
