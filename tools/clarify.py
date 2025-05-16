import re
from typing import Dict, Optional
import logging
from datetime import datetime
import dateparser  # ✅ 추가

logger = logging.getLogger(__name__)

REGISTER_KEYWORDS = ["등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"]
DELETE_KEYWORDS = ["삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어", "제거해"]
UPDATE_KEYWORDS = ["수정", "변경", "바꿔", "미뤄", "조정", "업데이트", "늦게", "앞당겨", "취소하고", "대신", "반영해"]

CATEGORY_KEYWORDS = ["회의", "미팅", "약속", "상담", "콘텐츠", "개인", "시공", "공사"]

# 날짜 표현 정규식
DATE_PATTERNS = [
    r"\d{1,2}월\s*\d{1,2}일\s*(오전|오후)?\s*\d{1,2}시",
    r"\d{1,2}월\s*\d{1,2}일",
    r"오늘", r"내일", r"모레", r"다음주\s*[월화수목금토일]요일"
]

def clarify_command(message: str) -> Dict[str, Optional[str]]:
    """
    명령어에서 title, date, category, intent 등을 추출합니다.
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
        date_regex = "|".join(DATE_PATTERNS)
        full_date_match = re.search(date_regex, message)
        if full_date_match:
            date_str = full_date_match.group(0).strip()
            # ✅ dateparser로 미래 날짜 기준 보정 파싱
            parsed_date = dateparser.parse(
                date_str,
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": datetime.now(),  # 기준일을 오늘로
                    "TIMEZONE": "Asia/Seoul",
                    "RETURN_AS_TIMEZONE_AWARE": False
                }
            )
            if parsed_date:
                result["start_date"] = parsed_date.isoformat()
            else:
                logger.warning(f"[clarify] 날짜 파싱 실패: {date_str}")
        else:
            logger.warning(f"[clarify] 날짜 추출 실패: {message}")

        # title 추출 (날짜 이후 나오는 문장 → 등록해줘, 추가해줘 제거)
        if full_date_match:
            end = full_date_match.end()
            remaining = message[end:]
            result["title"] = (
                remaining.lstrip("에 ").replace("등록해줘", "")
                        .replace("추가해줘", "")
                        .replace("기록해줘", "")
                        .replace("예정", "")
                        .strip()
            )

        logger.debug(f"[clarify] 파싱 결과: {result}")
        return result

    except Exception as e:
        logger.error(f"[clarify] 파싱 오류: {str(e)}")
        return result
