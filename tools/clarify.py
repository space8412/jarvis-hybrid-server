import re
from typing import Tuple, Optional
from datetime import datetime, timedelta
import logging
from dateutil import parser
import jamo

logger = logging.getLogger(__name__)

# ✅ intent 분기 키워드 목록
REGISTER_KEYWORDS = [
    "등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"
]

DELETE_KEYWORDS = [
    "삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어", "제거해"
]

UPDATE_KEYWORDS = [
    "수정", "변경", "바꿔", "미뤄", "조정", "업데이트", "늦게", "앞당겨", "취소하고", "대신", "반영해"
]

def parse_korean_date(date_str: str) -> Optional[datetime]:
    """
    한국어 날짜 표현을 datetime 객체로 변환합니다.
    """
    now = datetime.now()

    try:
        if "오늘" in date_str:
            date = now
        elif "내일" in date_str:
            date = now + timedelta(days=1)
        elif "모레" in date_str:
            date = now + timedelta(days=2)
        elif "다음주" in date_str:
            date = now + timedelta(days=7)
        else:
            date = parser.parse(date_str, fuzzy=True)

        if "오전" in date_str or "오후" in date_str:
            time_match = re.search(r"(\d{1,2})시", date_str)
            if time_match:
                hour = int(time_match.group(1))
                if "오후" in date_str and hour < 12:
                    hour += 12
                date = date.replace(hour=hour, minute=0)

        return date
    except Exception as e:
        logger.error(f"날짜 파싱 실패: {date_str} - {str(e)}")
        return None

def clarify_command(message: str) -> Tuple[str, str, str, str]:
    """
    텍스트 메시지를 분석하여 title, date, category, intent를 추출합니다.
    """
    title = ""
    start_date = ""
    category = ""
    intent = ""

    try:
        date_patterns = [
            r"\d{1,2}월\s*\d{1,2}일",
            r"오늘",
            r"내일",
            r"모레",
            r"다음주\s*[월화수목금토일]요일"
        ]
        date_pattern = "|".join(date_patterns)

        # ✅ intent 분기 처리
        for word in REGISTER_KEYWORDS:
            if word in message:
                intent = "register_schedule"
                break

        for word in DELETE_KEYWORDS:
            if word in message:
                intent = "delete_schedule"
                break

        for word in UPDATE_KEYWORDS:
            if word in message:
                intent = "update_schedule"
                break

        # ✅ title 추출
        title_match = re.search(f"(.+?)({date_pattern})", message)
        if title_match:
            title = title_match.group(1).strip()

        # ✅ 날짜 추출
        date_match = re.search(date_pattern, message)
        if date_match:
            start_date = date_match.group(0)

        # ✅ 카테고리 키워드 추출 (간단한 키워드 기반)
        category_keywords = ["회의", "미팅", "약속", "상담", "콘텐츠", "개인", "시공", "공사"]
        for keyword in category_keywords:
            if keyword in message:
                category = keyword
                break

    except Exception as e:
        logger.error(f"명령 파싱 오류 발생: {str(e)}")

    # ✅ 파싱 결과 디버깅 로그
    logger.debug(f"[clarify_command] 파싱 결과 → title: {title}, date: {start_date}, category: {category}, intent: {intent}")

    return title, start_date, category, intent
