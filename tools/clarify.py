import re
import logging
from datetime import datetime
from typing import Dict
import dateparser
import dateparser.search
import openai
import os

logger = logging.getLogger(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

REGISTER_KEYWORDS = ["등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"]
DELETE_KEYWORDS = ["삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어"]
UPDATE_KEYWORDS = ["수정", "변경", "바꿔", "미뤄", "조정", "옮겨", "다시", "앞당겨", "뒤로", "이동"]
CATEGORY_KEYWORDS = ["회의", "미팅", "상담", "콘텐츠", "개인", "시공", "공사"]

def classify_intent(text: str) -> str:
    for k in REGISTER_KEYWORDS:
        if k in text:
            return "register_schedule"
    for k in DELETE_KEYWORDS:
        if k in text:
            return "delete_schedule"
    for k in UPDATE_KEYWORDS:
        if k in text:
            return "update_schedule"
    return "unknown"

def extract_category(text: str) -> str:
    for k in CATEGORY_KEYWORDS:
        if k in text:
            return k
    return "기타"

def extract_title(text: str) -> str:
    match = re.search(r"(.*?)(등록|삭제|수정|변경|추가|기록|잡아|저장)", text)
    if match:
        return match.group(1).strip().replace("로 잡힌", "").replace("로", "").strip()
    else:
        # fallback: 문장 끝에서 카테고리 키워드 추출
        for keyword in CATEGORY_KEYWORDS:
            if keyword in text:
                return keyword
        return text.strip()

def call_gpt_iso_dates(text: str) -> list:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"'{text}'라는 문장에서 등장하는 날짜/시간을 모두 ISO 8601 형식으로 변환해서 리스트로 출력해줘. 예: ['2025-05-23T14:00:00', '2025-05-23T15:00:00']"
            }],
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        return eval(result)
    except Exception as e:
        logger.error(f"[clarify] GPT ISO 추출 실패: {e}")
        return []

def clarify_command(text: str) -> Dict:
    intent = classify_intent(text)
    category = extract_category(text)
    title = extract_title(text)

    parsed = dateparser.search.search_dates(text, languages=["ko"]) or []
    dates = [d[1].isoformat() for d in parsed] if parsed else []

    # fallback: GPT 보정
    if not dates:
        logger.warning(f"[clarify] dateparser 실패 → GPT 보정 시도: {text}")
        gpt_dates = call_gpt_iso_dates(text)
        dates = gpt_dates if isinstance(gpt_dates, list) else []

    if intent == "update_schedule":
        origin_date = dates[0] if len(dates) >= 1 else ""
        start_date = dates[1] if len(dates) >= 2 else ""
    else:
        origin_date = ""
        start_date = dates[0] if dates else ""

    return {
        "intent": intent,
        "title": title,
        "start_date": start_date,
        "category": category,
        "origin_title": title if intent == "update_schedule" else "",
        "origin_date": origin_date if intent == "update_schedule" else ""
    }
