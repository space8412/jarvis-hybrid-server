import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request  # ✅ 토큰 갱신용

logger = logging.getLogger(__name__)

# ✅ 인증 처리
creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
if not creds_json:
    raise RuntimeError("❌ GOOGLE_CALENDAR_CREDENTIALS 환경변수가 없습니다.")

creds_data = json.loads(creds_json)
creds = Credentials.from_authorized_user_info(
    creds_data, ["https://www.googleapis.com/auth/calendar"]
)

# ✅ 만료된 경우 토큰 자동 갱신
if creds.expired and creds.refresh_token:
    try:
        creds.refresh(Request())
        logger.info("🔄 Google Calendar 토큰 자동 갱신 완료")
    except Exception as e:
        logger.error(f"❌ Google Calendar 토큰 갱신 실패: {e}")
        raise RuntimeError("Google Calendar 인증 갱신 실패")

calendar_service = build("calendar", "v3", credentials=creds)

# ✅ 제목 정규화 함수
def normalize_title(text: str) -> str:
    return " ".join(text.lower().split())

# ✅ 일정 삭제 함수
def delete_schedule(title: str, start_date: str, category: str) -> str:
    try:
        # ✅ ISO 8601 형식 지원
        parsed_datetime = datetime.fromisoformat(start_date)
        date_str = parsed_datetime.strftime("%Y-%m-%d")
        time_min = f"{date_str}T00:00:00+09:00"
        time_max = f"{date_str}T23:59:59+09:00"

        # ✅ 일정 조회
        events_result = calendar_service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return f"{date_str}에는 등록된 일정이 없습니다."

        expected = normalize_title(f"[{category}] {title}")
        deleted_count = 0

        for event in events:
            event_title = normalize_title(event.get("summary", ""))
            if event_title == expected:
                calendar_service.events().delete(
                    calendarId="primary",
                    eventId=event["id"]
                ).execute()
                deleted_count += 1

        if deleted_count == 0:
            return f"{date_str}에는 '{title}' 일정이 없습니다."
        else:
            return f"{date_str} '{title}' 일정 {deleted_count}건 삭제 완료."

    except Exception as e:
        logger.error(f"❌ 일정 삭제 중 오류: {str(e)}")
        raise
