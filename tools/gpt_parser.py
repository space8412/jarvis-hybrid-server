import os
import json
from openai import OpenAI

# ✅ GPT API 키 불러오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def parse_command(text: str) -> dict:
    """
    GPT를 호출하여 자연어 명령어를 intent, title, date, category 등으로 분석
    """
    prompt = f"""
    다음 명령어를 분석해서 JSON으로 반환해줘. 조건은 다음과 같아:
    - intent: register_schedule, delete_schedule, update_schedule 중 하나
    - title: 장소나 키워드를 제목으로 사용
    - date: ISO 8601 형식으로 (예: 2024-05-15T15:00:00)
    - category: 회의, 상담, 시공, 공사, 미정 등 중 하나
    명령어: {text}
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 일정 자동화를 위한 분석 비서야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("GPT 응답이 JSON 형식이 아닙니다.")

    return result
