import re
import openai
import json
from typing import Optional, Dict

def clarify_command(command: str) -> Dict[str, Optional[str]]:
    def extract_command_details(command: str) -> Dict[str, Optional[str]]:
        # 정규식을 사용하여 title, start_date, origin_date, intent, category, origin_title 추출 시도
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

        # intent가 register_schedule이면 origin_title과 origin_date는 None으로 고정
        if result['intent'] == 'register_schedule':
            result['origin_title'] = None
            result['origin_date'] = None

        # 정규식으로 추출에 실패한 경우, GPT 보정 로직 사용
        if not all(result.values()):
            result = gpt_correction(command)

        return result

    def gpt_correction(command: str) -> Dict[str, Optional[str]]:
        # OpenAI API를 사용하여 title, start_date, origin_date, intent, category, origin_title 추출 시도
        prompt = (
            f"Extract title, start_date, origin_date, intent, category, and origin_title "
            f"from the following command:\n\n{command}\n\n"
            f"Format the response as a JSON object with keys "
            f"'title', 'start_date', 'origin_date', 'intent', 'category', and 'origin_title'."
        )

        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.7
        )

        gpt_result = response.choices[0].text.strip()

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

        # title 최대 20자 제한
        if result['title']:
            result['title'] = result['title'][:20]

        # category가 없으면 기본값 '기타'로 설정
        if not result['category']:
            result['category'] = '기타'

        # intent가 register_schedule이면 origin_title과 origin_date는 None으로 고정
        if result['intent'] == 'register_schedule':
            result['origin_title'] = None
            result['origin_date'] = None

        return result

    return extract_command_details(command)
