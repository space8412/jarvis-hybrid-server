import re
import logging
from typing import Dict, Optional
from datetime import datetime
import dateparser

logger = logging.getLogger(__name__)

REGISTER_KEYWORDS = ["등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"]
DELETE_KEYWORDS = ["삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어", "제거해"]
UPDATE_KEYWORDS = ["수정", "변경", "바꿔", "미뤄", "조정", "업데이트", "늦게", "앞당겨", "취소하고", "대신", "반영해"]

CATEGORY_KEYWORDS = ["회의", "미팅", "약속", "상담", "콘텐츠", "개인", "시공", "공사"]

def extract_datetime(text: str) -> Optional[str]:
    dt = dateparser.parse(text, languages=["ko"], settings={"PREFER_DATES_FROM": "future"})
    if dt:
        return dt.isoformat()
    return None

def classify_category(text: str) -> str:
    for keyword in CATEGORY_KEYWORDS:
        if keyword in text:
            return keyword
    return "기타"

def clarify_command(text: str) -> Dict:
    logger.warning(f"[clarify] dateparser 실패 → GPT 보정 시도: {text}")
    from openai import OpenAI
    import os

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def gpt_extract(prompt: str) -> str:
        response = client.chat.completions.create(
            model="gpt-4",
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

    # ✅ intent 판별
    intent = "register_schedule"
    for word in DELETE_KEYWORDS:
        if word in text:
            intent = "delete_schedule"
            break
    for word in UPDATE_KEYWORDS:
        if word in text:
            intent = "update_schedule"
            break

    # ✅ category 판별
    category = classify_category(text)

    # ✅ origin_date (정규식 기반 추출)
    origin_date = ""
    origin_match = re.search(r"(?P<origin_time>\d{1,2}월\s*\d{1,2}일\s*(오전|오후)?\s*\d{1,2}시?)\s*로\s*잡힌", text)
    if origin_match:
        origin_time_str = origin_match.group("origin_time")
        origin_date = extract_datetime(origin_time_str) or ""

    # ✅ origin_title (정규식 기반 추출)
    origin_title = ""
    title_match = re.search(r"잡힌\s*(?P<title>[\w\s가-힣]+?)\s*(을|를)?\s*(3시|수정|변경|바꿔|미뤄|조정|업데이트|앞당겨|늦게)", text)
    if title_match:
        origin_title = title_match.group("title").strip()

    # ✅ GPT를 통한 변경 후 날짜 추출
    start_date = ""
    time_prompt = f"'{text}'라는 문장에서 언급된 날짜/시간을 ISO 8601 형식으로 변환해줘.\n기준: 2025년 한국 시간 (Asia/Seoul), 결과는 예: '2025-05-20T14:00:00'\n결과는 한 줄짜리 ISO 날짜 문자열만 출력해줘. 설명 없이 결과만 줘."
    try:
        start_date = gpt_extract(time_prompt)
        logger.info(f"[clarify] GPT 보정 성공 → {start_date}")
    except Exception as e:
        logger.error(f"[clarify] GPT 보정 실패: {e}")
        start_date = ""

    # ✅ 최종 title 결정 (origin_title → fallback)
    title = origin_title
    if not title:
        fallback_title_match = re.search(r"(?P<title>[\w\s가-힣]+?)\s*(을|를)?\s*(등록|삭제|수정|변경|기록|추가)", text)
        title = fallback_title_match.group("title").strip() if fallback_title_match else ""

    return {
        "intent": intent,
        "title": title,
        "start_date": start_date,
        "category": category,
        "origin_title": origin_title if intent == "update_schedule" else "",
        "origin_date": origin_date if intent == "update_schedule" else ""
    }
