import re
import openai
import json
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

def clarify_command(command: str) -> Dict[str, Optional[str]]:
    def extract_command_details(command: str) -> Dict[str, Optional[str]]:
        title_pattern = r'title:\s*(.+?)\s*(?:,|$)'
        start_date_pattern = r'start_date:\s*(\d{4}-\d{2}-\d{2})'
        origin_date_pattern = r'origin_date:\s*(\d{4}-\d{2}-\d{2})'
        intent_pattern = r'intent:\s*(.+?)\s*(?:,|$)'
        category_pattern = r'category:\s*(.+?)\s*(?:,|$)'
        origin_title_pattern = r'origin_title:\s*(.+?)\s*(?:,|$)'

        result = {
            'title': None,
            'start_date': None,
            'origin_date': None,
            'intent': None,
            'category': '기타',
            'origin_title': None
        }

        title_match = re.search(title_pattern, command)
        if title_match:
            result['title'] = title_match.group(1)[:20]

        for pattern, key in [
            (start_date_pattern, "start_date"),
            (origin_date_pattern, "origin_date"),
            (intent_pattern, "intent"),
            (category_pattern, "category"),
            (origin_title_pattern, "origin_title"),
        ]:
            match = re.search(pattern, command)
            if match:
                result[key] = match.group(1)

        # origin_title/origin_date는 register일 경우 무시
        if result['intent'] == 'register_schedule':
            result['origin_title'] = None
            result['origin_date'] = None

        # 일부라도 None이면 GPT 보정
        if not all([result["title"], result["start_date"], result["intent"]]):
            result = gpt_correction(command)

        return result

    def gpt_correction(command: str) -> Dict[str, Optional[str]]:
        prompt = f"""
너는 일정관리 AI야.
다음 명령어에서 title, start_date, origin_date, intent, category, origin_title 값을 추출해서 반드시 아래 JSON 형식 그대로 출력해줘.

명령어:
{command}

결과는 아래 형식처럼 무조건 JSON으로 줘:
{{
  "title": "...",
  "start_date": "...",
  "origin_date": "...",
  "intent": "...",
  "category": "...",
  "origin_title": "..."
}}

설명 없이 JSON만 출력해. 문자열 내에 작은따옴표(')가 아니라 큰따옴표(")를 사용해.
        """.strip()

        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            gpt_result = response.choices[0].message.content.strip()
            logger.debug(f"[gpt_correction] raw response: {gpt_result}")

            result = json.loads(gpt_result)
        except Exception as e:
            logger.error(f"[gpt_correction] GPT 오류: {e}")
            result = {
                'title': None,
                'start_date': None,
                'origin_date': None,
                'intent': None,
                'category': '기타',
                'origin_title': None
            }

        if result.get("title"):
            result["title"] = result["title"][:20]
        if not result.get("category"):
            result["category"] = "기타"
        if result.get("intent") == "register_schedule":
            result["origin_title"] = None
            result["origin_date"] = None

        return result

    return extract_command_details(command)
