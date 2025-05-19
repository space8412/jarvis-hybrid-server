import re
import json
import os
from typing import Optional, Dict
from openai import OpenAI

# ✅ 클라이언트 객체 생성
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clarify_command(command: str) -> Dict[str, Optional[str]]:
    def extract_command_details(command: str) -> Dict[str, Optional[str]]:
        title_pattern = r'title:\s*(.+?)\s*(?:,|$)'
        start_date_pattern = r'start_date:\s*(\d{4}-\d{2}-\d{2})'
        origin_date_pattern = r'origin_date:\s*(\d{4}-\d{2}-\d{2})'
        intent_pattern = r'intent:\s*(.+?)\s*(?:,|$)'
        category_pattern = r'category:\s*(.+?)\s*(?:,|$)'
        origin_title_pattern = r'origin_title:\s*(.+?)\s*(?:,|$)'

        title_match = re.search(title_pattern, command)
        start_date_match = re.search(start_date_pattern, command)
        origin_date_match = re.search(origin_date_pattern, command)
        intent_match = re.search(intent_pattern, command)
        category_match = re.search(category_pattern, command)
        origin_title_match = re.search(origin_title_pattern, command)

        result = {
            'title': title_match.group(1)[:20] if title_match else None,
            'start_date': start_date_match.group(1) if start_date_match else None,
            'origin_date': origin_date_match.group(1) if origin_date_match else None,
            'intent': intent_match.group(1) if intent_match else None,
            'category': category_match.group(1) if category_match else '기타',
            'origin_title': origin_title_match.group(1) if origin_title_match else None
        }

        if result['intent'] == 'register_schedule':
            result['origin_title'] = None
            result['origin_date'] = None

        if not all(result.values()):
            result = gpt_correction(command)

        return result

    def gpt_correction(command: str) -> Dict[str, Optional[str]]:
        today = "2025-05-19"  # 기준일 고정
        tomorrow = "2025-05-20"
        day_after_tomorrow = "2025-05-21"

        prompt = f"""
오늘 날짜는 {today}야.
너는 일정관리 AI야.
다음 명령어에서 title, start_date, origin_date, intent, category, origin_title 값을 추출해서 반드시 아래 JSON 형식 그대로 출력해줘.

📌 intent 값은 반드시 아래 중 하나로만 써야 해:
- "register_schedule"
- "update_schedule"
- "delete_schedule"

📌 category 값은 반드시 아래 중 하나로 한글로만 써야 해:
- 회의
- 상담
- 시공
- 공사
- 콘텐츠
- 개인
- 현장방문
- 기타

📌 날짜 해석 규칙 (매우 중요):
- 오늘은 {today}
- "내일"은 {tomorrow}
- "모레", "내일모레"는 {day_after_tomorrow}
- "어제", "그제"도 오늘을 기준으로 정확히 해석해
- 절대 '내일모레 = 3일 후'처럼 해석하지 마

❗ 주의사항:
- "수정", "변경", "바꿔" 등이 포함된 문장은 intent가 "update_schedule"이야.
- 이 경우 "등록된 일정" 앞에 나온 날짜와 제목은 origin_date, origin_title이야.
- "으로 바꿔줘" 또는 "로 바꿔줘" 뒤에 나온 내용은 새로운 일정이야. → start_date, title

명령어:
{command}

반드시 아래 형식처럼 JSON만 출력해:
{{
  "title": "...",
  "start_date": "...",
  "origin_date": "...",
  "intent": "...",
  "category": "...",
  "origin_title": "..."
}}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0
        )

        gpt_result = response.choices[0].message.content.strip()
        try:
            result = json.loads(gpt_result)
        except json.JSONDecodeError:
            result = {
                'title': None,
                'start_date': None,
                'origin_date': None,
                'intent': None,
                'category': '기타',
                'origin_title': None
            }

        if result['title']:
            result['title'] = result['title'][:20]

        if not result['category']:
            result['category'] = '기타'

        if result['intent'] == 'register_schedule':
            result['origin_title'] = None
            result['origin_date'] = None

        return result

    return extract_command_details(command)
