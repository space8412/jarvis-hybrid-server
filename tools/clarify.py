import re
import os
import json
import logging
from typing import Optional, Dict
from openai import OpenAI

logger = logging.getLogger(__name__)
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
        prompt = (
            f"다음 명령문에서 title, start_date, origin_date, intent, category, origin_title 값을 추출해서 "
            f"JSON 형식으로 반환해줘:\n\n"
            f"{command}\n\n"
            f"출력 예시: {{\"title\": \"후암동 회의\", \"start_date\": \"2025-05-23T14:00:00\", "
            f"\"origin_date\": \"2025-05-20T14:00:00\", \"intent\": \"update_schedule\", "
            f"\"category\": \"회의\", \"origin_title\": \"후암동 회의\"}}"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            gpt_result = response.choices[0].message.content.strip()
            result = json.loads(gpt_result)
        except Exception as e:
            logger.error(f"[clarify] GPT 호출 또는 JSON 파싱 오류: {e}")
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

        logger.info(f"[clarify] GPT 보정 최종 적용 → {result}")
        return result

    return extract_command_details(command)
