import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# ✅ 환경변수에서 인증 정보 로딩
try:
    creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
    creds_data = json.loads(creds_json)
except json.JSONDecodeError:
    logger.error("❌ GOOGLE_CALENDAR_CREDENTIALS JSON 형식 오류")
    raise RuntimeError("Google Calendar 인증 정보 파싱 실패")

# ✅ 인증 객체 생성
creds = Credentials.from_authorized_user_info(creds_data, ["https://www.googleapis.com/auth/calendar"])

# ✅ 토큰 만료 시 자동 갱신
if creds.expired and creds.refresh_token:
    try:
        creds.refresh(Request())
        logger.info("🔄 Google Calendar 토큰 자동 갱신 완료")
    except Exception as e:
        logger.error(f"❌ Google Calendar 토큰 갱신 실패: {e}")
        raise RuntimeError("Google Calendar 인증 갱신 실패")

calendar_service = build("calendar", "v3", credentials=creds)

# ✅ 제목 비교 정규화 함수
def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())

# ✅ 시간 비교 허용 함수 (±5분 이내)
def is_same_time(t1_str: str, t2_str: str, minute_range=5) -> bool:
    try:
        t1 = datetime.fromisoformat(t1_str.replace(" ", "T"))
        t2 = datetime.fromisoformat(t2_str.replace(" ", "T"))
        return abs((t1 - t2).total_seconds()) <= minute_range * 60
    except Exception:
        return False

# ✅ 일정 수정 API 재시도 래퍼
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def update_calendar_event(calendar_service, event_id, event_body):
    return calendar_service.events().patch(
        calendarId="primary",
        eventId=event_id,
        body=event_body
    ).execute()

# ✅ 메인 함수
def update_schedule(origin_title: str, origin_date: str, new_date: str, category: str):
    try:
        if not origin_date:
            logger.error("❌ origin_date 값이 비어 있습니다. 기존 일정을 찾을 수 없습니다.")
            return {"status": "fail", "reason": "origin_date missing"}

        origin_day = datetime.fromisoformat(origin_date).date()
        new_datetime = datetime.fromisoformat(new_date)

        time_min = f"{origin_day}T00:00:00+09:00"
        time_max = f"{origin_day}T23:59:59+09:00"

        events_result = calendar_service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if not events:
            logger.warning(f"⚠️ 해당 날짜({origin_day})에 등록된 일정이 없습니다.")
            return {"status": "fail", "reason": "no events on that day"}

        origin_norm = normalize_title(origin_title)

        # ✅ 일정 찾기 (title 포함 + ±5분 시간 차이 허용)
        target_event = None
        for event in events:
            summary = normalize_title(event.get("summary", ""))
            start_str = event["start"].get("dateTime") or event["start"].get("date")
            if origin_norm in summary and is_same_time(start_str, origin_date):
                target_event = event
                break

        if not target_event:
            logger.warning(f"⚠️ '{origin_title}' 일정({origin_date})을 찾을 수 없습니다.")
            return {"status": "fail", "reason": "event not found"}

        event_id = target_event["id"]

        if "dateTime" in target_event["start"]:
            old_start = datetime.fromisoformat(target_event["start"]["dateTime"])
            old_end = datetime.fromisoformat(target_event["end"]["dateTime"])
            duration = old_end - old_start

            new_start = new_datetime
            new_end = new_start + duration

            event_body = {
                "summary": f"[{category}] {origin_title}",
                "start": {
                    "dateTime": new_start.isoformat(),
                    "timeZone": "Asia/Seoul"
                },
                "end": {
                    "dateTime": new_end.isoformat(),
                    "timeZone": "Asia/Seoul"
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 120},
                        {"method": "popup", "minutes": 60 * 24 - 240}
                    ]
                }
            }
        else:
            event_body = {
                "summary": f"[{category}] {origin_title}",
                "start": {"date": new_datetime.date().isoformat()},
                "end": {"date": new_datetime.date().isoformat()},
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 60 * 24}
                    ]
                }
            }

        update_calendar_event(calendar_service, event_id, event_body)
        logger.info(f"✅ 일정 수정 완료: '{origin_title}' → {new_date}")
        return {"status": "success", "event_id": event_id}

    except Exception as e:
        logger.error(f"❌ 일정 수정 중 오류 발생: {e}")
        return {"status": "error", "reason": str(e)}
