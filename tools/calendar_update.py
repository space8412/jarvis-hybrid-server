import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# ✅ 환경변수에서 인증 정보 로딩
try:
    creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
    creds_data = json.loads(creds_json)
except json.JSONDecodeError:
    logger.error("❌ GOOGLE_CALENDAR_CREDENTIALS JSON 형식 오류")
    raise RuntimeError("Google Calendar 인증 정보 파싱 실패")

creds = Credentials.from_authorized_user_info(creds_data, ["https://www.googleapis.com/auth/calendar"])
calendar_service = build("calendar", "v3", credentials=creds)

# ✅ 제목 비교 정규화 함수
def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())

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
    """
    기존 일정을 찾아 새로운 날짜로 수정합니다.
    """
    try:
        # ✅ 날짜 포맷 검증
        try:
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"❌ 잘못된 날짜 형식: {new_date}")
            raise ValueError("날짜 형식은 YYYY-MM-DD 이어야 합니다.")

        # ✅ 검색 시간 범위 설정 (한국 시간 기준)
        time_min = f"{origin_date}T00:00:00+09:00"
        time_max = f"{origin_date}T23:59:59+09:00"

        events_result = calendar_service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])

        # ✅ 제목+카테고리 정규화 비교로 대상 이벤트 찾기
        expected_summary = normalize_title(f"[{category}] {origin_title}")
        target_event = next(
            (event for event in events if normalize_title(event["summary"]) == expected_summary),
            None
        )

        if not target_event:
            logger.warning(f"⚠️ '{origin_title}' 일정({origin_date})을 찾을 수 없습니다.")
            return

        event_id = target_event["id"]

        # ✅ 시간 포함 일정 처리
        if "dateTime" in target_event["start"]:
            old_start = datetime.fromisoformat(target_event["start"]["dateTime"])
            old_end = datetime.fromisoformat(target_event["end"]["dateTime"])
            duration = old_end - old_start

            new_start = datetime.strptime(new_date, "%Y-%m-%d").replace(
                hour=old_start.hour,
                minute=old_start.minute
            )
            new_end = new_start + duration

            event_body = {
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

        # ✅ 종일 일정 처리
        else:
            event_body = {
                "start": {"date": new_date},
                "end": {"date": new_date},
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": 60 * 24}
                    ]
                }
            }

        # ✅ 일정 수정 실행
        update_calendar_event(calendar_service, event_id, event_body)
        logger.info(f"✅ 일정 수정 완료: '{origin_title}' → {new_date}")

    except Exception as e:
        logger.error(f"❌ 일정 수정 중 오류 발생: {str(e)}")
        raise
