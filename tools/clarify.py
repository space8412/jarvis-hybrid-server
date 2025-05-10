import openai
import os
import json
from dateutil import tz
from dateutil.parser import isoparse

openai.api_key = os.getenv("OPENAI_API_KEY")

def validate_and_parse(date_str):
    try:
        dt = isoparse(date_str)
        # 타임존 없는 경우 → 한국시간으로 명확히 설정
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz.gettz("Asia/Seoul"))
        else:
            dt = dt.astimezone(tz.gettz("Asia/Seoul"))
        # +09:00 포함된 ISO 8601 문자열로 반환
        return dt.isoformat()
    except Exception as e:
        print("❌ 날짜 파싱 오류:", date_str, e)
        return ""

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
        result = eval(content)  # dict 형식 응답 대응
    except:
        result = json.loads(content)  # JSON 형식 응답 대응

    # ✅ ISO 형식으로 KST 보정된 값 반환
    origin_date_kst = validate_and_parse(result.get("origin_date", ""))
    date_kst = validate_and_parse(result.get("date", ""))

    return {
        "intent": "update_schedule",
        "origin_title": result.get("origin_title", ""),
        "origin_date": origin_date_kst,
        "title": result.get("title", ""),
        "date": date_kst
    }
