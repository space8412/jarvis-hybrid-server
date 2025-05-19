import re
import logging
from datetime import datetime
import dateparser

logger = logging.getLogger(__name__)

REGISTER_KEYWORDS = ["등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"]
DELETE_KEYWORDS = ["삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어"]
UPDATE_KEYWORDS = ["수정", "변경", "바꿔", "미뤄", "조정", "앞당겨"]

CATEGORY_KEYWORDS = ["회의", "미팅", "상담", "시공", "공사", "콘텐츠", "개인"]

def clarify_command(text: str) -> dict:
    text = text.strip()
    intent = ""
    for keyword in REGISTER_KEYWORDS:
        if keyword in text:
            intent = "register_schedule"
            break
    for keyword in DELETE_KEYWORDS:
        if keyword in text:
            intent = "delete_schedule"
            break
    for keyword in UPDATE_KEYWORDS:
        if keyword in text:
            intent = "update_schedule"
            break

    # 날짜 추출
    parsed_date = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()})
    if not parsed_date:
        logger.warning("[clarify] dateparser 실패 → GPT 보정 시도: %s", text)
        from tools.gpt_utils import ask_date_correction
        try:
            gpt_result = ask_date_correction(text)
            parsed_date = dateparser.parse(gpt_result)
        except Exception as e:
            logger.warning(f"[clarify] GPT 보정 실패: {e}")
            parsed_date = None

    # 카테고리 추출
    category = next((c for c in CATEGORY_KEYWORDS if c in text), "기타")

    # 제목 추출 (핵심 키워드만 남기기)
    if intent == "register_schedule":
        title_match = re.search(r"(후암동\s*회의|회의|미팅|상담|시공|공사|콘텐츠|개인)", text)
        title = title_match.group(0) if title_match else "일정"
    elif intent == "update_schedule":
        origin_match = re.search(r"(\d{1,2}월\s*\d{1,2}일\s*(오전|오후)?\s*\d{0,2}시?)", text)
        origin_date_str = origin_match.group(0) if origin_match else ""
        origin_title_match = re.search(r"(후암동\s*회의|회의|미팅|상담|시공|공사|콘텐츠|개인)", text)
        origin_title = origin_title_match.group(0) if origin_title_match else ""
        return {
            "intent": "update_schedule",
            "title": origin_title + "로",
            "start_date": parsed_date.isoformat() if parsed_date else "",
            "category": category,
            "origin_title": origin_title,
            "origin_date": origin_date_str,
        }
    else:
        title = "일정"

    return {
        "intent": intent,
        "title": title,
        "start_date": parsed_date.isoformat() if parsed_date else "",
        "category": category,
        "origin_title": "",
        "origin_date": "",
    }
