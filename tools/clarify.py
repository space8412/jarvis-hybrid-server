import re
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
from dateutil import parser

logger = logging.getLogger(__name__)

REGISTER_KEYWORDS = ["등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"]
DELETE_KEYWORDS = ["삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어", "제거해"]
UPDATE_KEYWORDS = ["수정", "변경", "바꿔", "미뤄", "조정", "업데이트", "늦게", "앞당겨", "취소하고", "대신", "반영해"]

CATEGORY_KEYWORDS = ["회의", "미팅", "약속", "상담", "콘텐츠", "개인", "시공", "공사"]

DATE_PATTERNS = [
    r"\d{1,2}월\s*\d{1,2}일(\s*오전|\s*오후)?\s*\d{1,2}시?",
    r"\d{1,2}월\s*\d{1,2}일",
    r"오늘", r"내일", r"모레", r"다음주\s*[월화수목금토일]요일"
]

def clarify_command(message: str) -> Dict[str, Optional[str]]:
    """
    명령어에서 title, date, category, intent 등을 추출합니다.
    update나 delete의 경우 origin_title, origin_date도 시도 추출합니다.
    """
    result = {
        "title": "",
        "start_date": "",
        "category": "",
        "intent": "",
        "origin_title": "",
        "origin_date": ""
    }

    try:
        # intent 판별
        for word in REGISTER_KEYWORDS:
            if word in message:
                result["intent"] = "register_schedule"
                break
        for word in DELETE_KEYWORDS:
            if word in message:
                result["intent"] = "delete_schedule"
                break
        for word in UPDATE_KEYWORDS:
            if word in message:
                result["intent"] = "update_schedule"
                break

        # 카테고리 추출
        for keyword in CATEGORY_KEYWORDS:
            if keyword in message:
                result["category"] = keyword
                break

        # 날짜 추출
        date_matches = re.findall("|".join(DATE_PATTERNS), message)
        if date_matches:
            if result["intent"] == "update_schedule" and len(date_matches) >= 2:
                result["origin_date"] = date_matches[0].strip()
                result["start_date"] = date_matches[1].strip()
            else:
                result["start_date"] = date_matches[0].strip()

        # 제목 추출 시도
        if result["intent"] == "update_schedule":
            split_msg = re.split("|".join(DATE_PATTERNS), message)
            if len(split_msg) >= 3:
                result["origin_title"] = split_msg[0].strip()
                result["title"] = split_msg[2].strip()
            elif len(split_msg) == 2:
                result["origin_title"] = split_msg[0].strip()
                result["title"] = split_msg[1].strip()
        else:
            title_match = re.search(f"(.+?)({'|'.join(DATE_PATTERNS)})", message)
            if title_match:
                result["title"] = title_match.group(1).strip()

        logger.debug(f"[clarify] 파싱 결과: {result}")
        return result

    except Exception as e:
        logger.error(f"[clarify] 파싱 오류: {str(e)}")
        return result
