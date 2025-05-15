import os
import json
import logging
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from tools.notion_writer import create_notion_page

logger = logging.getLogger(__name__)

# ✅ 환경변수에서 token.json 내용 불러오기
creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
if not creds_json:
    logger.error("❌ GOOGLE_CALENDAR_CREDENTIALS 환경변수가 설정되지 않았습니다.")
    raise RuntimeError("구글 인증 정보 누락")

creds = Credentials.from_authorized_user_info(json.loads(creds_json), ["https://www.googleapis.com/auth/calendar"])
calendar_service = build("calendar", "v3", credentials=creds)

def register_schedule(title: str, start_date: str, category: str):
    """
    제목, 날짜, 카테고리를 받아 구글 캘린더에 일정을 등록합니다.
    
    :param title: 일정 제목
    :param start_date: 시작 날짜 (YYYY-MM-DD 형식)
    :param category: 일정 카테고리 (e.g. "회의")
    """
    try:
        event = {
            "summary": f"[{category}] {title}",
            "start": {
                "date": start_date,
            },
            "end": {
                "date": start_date,
            },
        }

        event = calendar_service.events().insert(calendarId="primary", body=event).execute()
        logger.info(f"일정이 등록되었습니다. (일정 ID: {event['id']})")

        create_notion_page(title, start_date, category)
    except Exception as e:
        logger.error(f"일정 등록 중 오류 발생: {str(e)}")
        raise
