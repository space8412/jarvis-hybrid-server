import re
from typing import Dict
import logging
from datetime import datetime
import dateparser
import openai
import os

logger = logging.getLogger(__name__)
openai.api_key = os.environ["OPENAI_API_KEY"]

# 🔹 키워드 정의
REGISTER_KEYWORDS = ["등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"]
DELETE_KEYWORDS = ["삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어"]
UPDATE_KEYWORDS = ["수정", "변경", "바꿔", "미뤄", "조정", "업데이트", "앞당겨", "연기", "대신", "반영해"]

CATEGORY_KEYWORDS = {
    "회의": ["회의", "미팅", "줌", "온라인회의", "컨퍼런스"],
    "상담": ["상담", "컨설팅", "전화"],
    "공사": ["공사", "하스리", "미장", "철거", "도장"],
    "시공": ["시공", "작업", "현장", "설치"],
    "콘텐츠": ["콘텐츠", "릴스", "영상", "사진", "업로드"],
    "개인": ["병원", "약속", "모임", "가족", "휴가"]
}


def extract_category(text: str) -> str:
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "기타"


def extract_intent(text: str) -> str:
    if any(kw in text for kw in REGISTER_KEYWORDS):
        return "register_schedule"
    elif any(kw in text for kw in DELETE_KEYWORDS):
        return "delete_schedule"
    elif any(kw in text for kw in UPDATE_KEYWORDS):
        return "update_schedule"
    else:
        return "unknown"


def extract_date_with_gpt(text: str) -> str:
    logger.warning("[clarify] dateparser 실패 → GPT 보정 시도: " + text)
    prompt = f"""
'5월 18일 오후 2시'은 2025년을 기준으로 한 한국 시간의 날짜와 시간입니다.
이를 ISO 8601 형식(예: 2025-05-18T14:00:00)으로 변환해줘.
결과는 날짜와 시간만 포함된 한 줄짜리 ISO 형식 문자열로만 줘.
불확실하더라도 예측해서 완성해줘.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=[{"role": "user", "content": prompt.replace("5월 18일 오후 2시", text)}]
    )
    date_str = response["choices"][0]["message"]["content"].strip()

    # 날짜만 있을 경우 T00:00:00 보완
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        date_str += "T00:00:00"
        logger.warning("[clarify] GPT 응답에 시간 없음 → T00:00:00 보완 적용")

    logger.info("[clarify] GPT 보정 성공 → " + date_str)
    return date_str


def extract_title(text: str) -> str:
    match = re.search(r"\d+[월.]\s*\d+[일.]?\s*(오전|오후)?\s*\d{1,2}시?", text)
    if match:
        return text[match.end():].strip().replace("등록해줘", "").replace("삭제해줘", "").replace("수정해줘", "").strip()
    return text


def clarify_command(text: str) -> Dict[str, str]:
    intent = extract_intent(text)
    category = extract_category(text)
    title = extract_title(text)

    parsed_date = dateparser.parse(text, languages=["ko"], settings={"PREFER_DATES_FROM": "future"})
    if parsed_date is None:
        start_date = extract_date_with_gpt(text)
    else:
        start_date = parsed_date.isoformat()

    origin_title = ""
    origin_date = ""

    # intent가 수정/삭제일 경우, 기존값이 있는지 예외적으로 추출 시도 (기본 구조 유지)
    if intent in ["update_schedule", "delete_schedule"]:
        origin_title = title
        origin_date = start_date

    logger.debug(f"[clarify] 파싱 결과: title={title}, start_date={start_date}, category={category}, intent={intent}")
    return {
        "title": title,
        "start_date": start_date,
        "category": category,
        "intent": intent,
        "origin_title": origin_title,
        "origin_date": origin_date
    }
