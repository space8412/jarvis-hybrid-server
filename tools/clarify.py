import re
import json
import os
from typing import Optional, Dict
from openai import OpenAI  # ✅ 최신 SDK

# ✅ OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clarify_command(command: str) -> Dict[str, Optional[str]]:
    def extract_command_details(command: str) -> Dict[str, Optional[str]]:
        # 정규식으로 필드 추출 시도
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

        # 등록 명령어일 경우 origin 필드는 제거
        if result['intent'] == 'register_schedule':
            result['origin_title'] = None
            result['origin_date'] = None

        # 하나라도 누락된 값이 있으면 GPT로 보정
        if not all(result.values()):
            result = gpt_correction(command)

        return result

    def gpt_correction(command: str) -> Dict[str, Optional[str]]:
        prompt = f"""
너는 일정관리 AI야.
다음 명령어에서 title, start_date, origin_date, intent, category, origin_title 값을 추출해서 반드시 아래 JSON 형식 그대로 출력해줘.

📌 intent 값은 반드시 아래 중 하나로만 써야 해:
- "register_schedule"
- "update_schedule"
- "delete_schedule"

기준 시점은 2025년 한국 시간 (Asia/Seoul)이고, 과거 날짜도 그대로 사용해.

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
            model="gpt-3.5-turbo",  # ✅ 비용 절감용 모델 적용됨
            messages=[
                {"role": "user", "content": prompt.strip()}
            ],
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

        # title 길이 제한
        if result['title']:
            result['title'] = result['title'][:20]

        # category 기본값
        if not result['category']:
            result['category'] = '기타'

        # 등록 intent 시 origin 값 제거
        if result['intent'] == 'register_schedule':
            result['origin_title'] = None
            result['origin_date'] = None

        return result

    return extract_command_details(command)
