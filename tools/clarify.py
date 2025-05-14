import re
from typing import Tuple

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
    
    # 일정 등록 intent 분석
    if "등록" in message or "추가" in message:
        intent = "register_schedule"
        title_match = re.search(r"(.+)(\s*\d{1,2}월\s*\d{1,2}일)", message)
        if title_match:
            title = title_match.group(1).strip()
        
        date_match = re.search(r"(\d{1,2}월\s*\d{1,2}일)", message)
        if date_match:  
            start_date = date_match.group(1)
        
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