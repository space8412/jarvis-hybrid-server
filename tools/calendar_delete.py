import os
import json
import logging
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

# ✅ 환경변수로부터 인증 정보 불러오기
creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
if not creds_json:
    logger.error("❌ GOOGLE_CALENDAR_CREDENTIALS 환경변수가 없습니다.")
    raise RuntimeError("Google Calendar 인증 정보 누락")

creds = Credentials.from_authorized_user_info(
    json.loads(creds_json),
    ["https://www.googleapis.com/auth/calendar"]
)
calendar_service = build("calendar", "v3", credentials=creds)

def delete_schedule(start_date: str):
    """
    시작 날짜 (YYYY-MM-DD 형식)를 받아 해당 날짜의 일정을 모두 삭제합니다.
    """
    try:
        # ✅ ISO 형식만 허용
        try:
            date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"❌ 날짜 형식 오류: '{start_date}' → 'YYYY-MM-DD' 형식이어야 합니다.")

        time_min = date_obj.strftime("%Y-%m-%dT00:00:00Z")
        time_max = date_obj.strftime("%Y-%m-%dT23:59:59Z")

        events_result = calendar_service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])

        if not events:
            logger.info(f"🟡 {start_date}에는 삭제할 일정이 없습니다.")
            return

        for event in events:
            calendar_service.events().delete(
                calendarId="primary", eventId=event["id"]
            ).execute()

        logger.info(f"🗑️ {start_date} 일정 {len(events)}건 삭제 완료.")

    except Exception as e:
        logger.error(f"❌ 일정 삭제 실패: {e}")
        raise
