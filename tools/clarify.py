import openai
import os
import json

openai.api_key = os.getenv("OPENAI_API_KEY")

def clarify_schedule_update(text: str):
    system_prompt = """너는 일정 관리 비서야. 사용자의 명령에서 다음 정보를 추출해:
- 기존 일정 제목 (origin_title)
- 기존 일정 시작 시간 (origin_date, ISO 8601 형식으로)
- 변경될 제목 (title) - 변경 없으면 빈 문자열
- 변경될 시간 (date, ISO 8601 형식) - 변경 없으면 빈 문자열

예시는 다음과 같아:
"5월 6일 오후 3시에 회의를 오후 4시 미팅으로 바꿔줘"
→ {
  "origin_title": "회의",
  "origin_date": "2025-05-06T15:00:00+09:00",
  "title": "미팅",
  "date": "2025-05-06T16:00:00+09:00"
}

단, 시간이나 제목 중 변경 요소가 없다면 빈 문자열로 남겨.
반드시 JSON 형태로 반환해."""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.2
    )

    content = response["choices"][0]["message"]["content"]

    try:
        result = eval(content)  # 파이썬 dict로 응답될 때
    except:
        result = json.loads(content)  # JSON 형식 대응

    return {
        "origin_title": result.get("origin_title", ""),
        "origin_date": result.get("origin_date", ""),
        "title": result.get("title", ""),
        "date": result.get("date", "")
    }
