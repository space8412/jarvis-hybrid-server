import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from tools.notion_writer import create_notion_page

creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/calendar"])
calendar_service = build("calendar", "v3", credentials=creds)

def register_schedule(title: str, start_date: str, category: str):
    """
    제목, 날짜, 카테고리를 받아 구글 캘린더에 일정을 등록합니다.
    
    :param title: 일정 제목
    :param start_date: 시작 날짜 (e.g. "5월 20일")
    :param category: 일정 카테고리 (e.g. "회의")
    """
    start_date_obj = datetime.strptime(start_date, "%m월 %d일")
    start_date_str = start_date_obj.strftime("%Y-%m-%d")
    
    event = {
        "summary": f"[{category}] {title}",
        "start": {
            "date": start_date_str,
        },
        "end": {
            "date": start_date_str,
        },
    }
    
    try:
        event = calendar_service.events().insert(calendarId="primary", body=event).execute()
        print(f"일정이 등록되었습니다. (일정 ID: {event['id']})")
    except Exception as e:
        print(f"일정 등록 중 오류 발생: {e}")
        
    create_notion_page(title, start_date_str, category)