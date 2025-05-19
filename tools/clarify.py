import os
import logging
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# 구글 서비스 연결
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "credentials.json"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=credentials)
calendar_id = "primary"  # 필요 시 환경변수로 분리 가능

def find_event_id_by_title_and_date(title: str, date_str: str):
    try:
        time_min = datetime.fromisoformat(date_str) - timedelta(minutes=5)
        time_max = datetime.fromisoformat(date_str) + timedelta(minutes=5)

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min.isoformat() + "Z",
            timeMax=time_max.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])

        for event in events:
            if event.get("summary") == title:
                return event["id"]
        return None
    except Exception as e:
        logger.error(f"[find_event_id_by_title_and_date] 오류 발생: {e}")
        return None

def update_schedule(data):
    try:
        origin_title = data.get("origin_title")
        origin_date = data.get("origin_date")
        if not origin_title or not origin_date:
            raise ValueError("origin_title 또는 origin_date가 누락되었습니다.")

        event_id = find_event_id_by_title_and_date(origin_title, origin_date)
        if not event_id:
            raise ValueError("기존 일정을 찾을 수 없습니다.")

        new_title = data.get("title", origin_title)
        new_date_str = data.get("start_date", origin_date)

        start_dt = datetime.fromisoformat(new_date_str)
        end_dt = start_dt + timedelta(hours=1)

        event = {
            "summary": new_title,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Asia/Seoul",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Asia/Seoul",
            },
        }

        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event,
        ).execute()

        logger.info(f"✅ Google Calendar 일정 수정 완료 (ID: {event_id})")
        return {"status": "success", "event_id": event_id}

    except Exception as e:
        logger.error(f"❌ Google Calendar 일정 수정 실패: {e}")
        return {"status": "error", "message": str(e)}
