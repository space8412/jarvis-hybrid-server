import re
from typing import Tuple
from datetime import datetime, timedelta
import logging
from dateutil import parser
from dateutil.relativedelta import relativedelta
import jamo

logger = logging.getLogger(__name__)

def parse_korean_date(date_str: str) -> datetime:
    """
    한국어 날짜 표현을 datetime 객체로 변환합니다.
    
    :param date_str: 한국어 날짜 문자열 (예: "내일 오후 3시", "다음주 월요일")
    :return: datetime 객체
    """
    now = datetime.now()
    
    # 상대적 날짜 처리
    if "내일" in date_str:
        date = now + timedelta(days=1)
    elif "모레" in date_str:
        date = now + timedelta(days=2)
    elif "다음주" in date_str:
        date = now + timedelta(days=7)
    else:
        # 절대적 날짜 처리 (예: "5월 20일")
        try:
            date = parser.parse(date_str, fuzzy=True)
        except:
            logger.error(f"날짜 파싱 실패: {date_str}")
            return now
    
    # 시간 처리
    if "오전" in date_str or "오후" in date_str:
        time_match = re.search(r"(\d{1,2})시", date_str)
        if time_match:
            hour = int(time_match.group(1))
            if "오후" in date_str and hour < 12:
                hour += 12
            date = date.replace(hour=hour, minute=0)
    
    return date

def clarify_command(message: str) -> Tuple[str, str, str, str]:
    """
    텍스트 메시지를 분석하여 title, date, category, intent를 추출합니다.
    
    :param message: 분석할 메시지 텍스트 
    :return: (title, date, category, intent) 튜플
    """
    title = ""
    start_date = ""
    category = ""
    intent = ""
    
    try:
        # 일정 등록 intent 분석
        if "등록" in message or "추가" in message:
            intent = "register_schedule"
            
            # 제목 추출 (날짜 이전의 모든 텍스트)
            date_patterns = [
                r"\d{1,2}월\s*\d{1,2}일",
                r"내일",
                r"모레",
                r"다음주\s*[월화수목금토일]요일"
            ]
            date_pattern = "|".join(date_patterns)
            
            title_match = re.search(f"(.+?)({date_pattern})", message)
            if title_match:
                title = title_match.group(1).strip()
            
            # 날짜 추출
            date_match = re.search(date_pattern, message)
            if date_match:
                start_date = date_match.group(0)
        
        category_keywords = ["회의", "미팅", "약속", "휴가", "이벤트"]
        for keyword in category_keywords:
            if keyword in message:
                category = keyword
                break
                
    # 일정 삭제 intent 분석        
    elif "삭제" in message or "제거" in message:
        intent = "delete_schedule"
        date_match = re.search(r"(\d{1,2}월\s*\d{1,2}일)", message)
        if date_match:
            start_date = date_match.group(1)
            
    return title, start_date, category, intent