import os
import json
import logging
from datetime import datetime
from dateutil import parser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request  # 🔹 추가

from tools.notion_writer import save_to_notion  # ✅ 수정된 import

logger = logging.getLogger(__name__)

# ✅ 환경변수에서 token.json 내용 불러오기
creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
if not creds_json:
    logger.error("❌ GOOGLE_CALENDAR_CREDENTIALS 환경변수가 설정되지 않았습니다.")
    raise RuntimeError("구글 인증 정보 누락")

# ✅ 구글 인증 정보 객체 생성
creds = Credentials.from_authorized_user_info(
    json.loads(creds_json),
    ["https://www.googleapis.com/auth/calendar"]
)

# ✅ 만료된 경우 토큰 자동 갱신
if creds.expired and creds.refresh_token:
    try:
        creds.refresh(Request())
        logger.info("🔄 Google Calendar 토큰 자동 갱신 완료")
    except Exception as e:
        logger.error(f"❌ Google Calendar 토큰 갱신 실패: {e}")
        raise RuntimeError("Google Calendar 인증 갱신 실패")

# ✅ 캘린더 서비스 초기화
calendar_service = build("calendar", "v3", credentials=creds)

def register_schedule(title: str, start_date: str, category: str):
    """
    제목, 날짜, 카테고리를 받아 구글 캘린더에 일정을 등록하고 Notion에 기록합니다.
    :param title: 일정 제목
    :param start_date: 시작 날짜 (예: "2025-05-18T14:00:00")
    :param category: 일정 카테고리
    """
    try:
        # ✅ 날짜 문자열 파싱 → datetime 객체
        try:
            parsed_dt = parser.parse(start_date)
        except Exception as e:
            logger.error(f"❌ 날짜 파싱 실패: {start_date} - {e}")
            raise ValueError(f"날짜 형식이 잘못되었습니다: {start_date}")

        # ✅ 시간 포함 여부 판단
        is_all_day = parsed_dt.hour == 0 and parsed_dt.minute == 0

        # ✅ ISO 형식 구성
        if is_all_day:
            calendar_start = {"date": parsed_dt.strftime("%Y-%m-%d")}
            calendar_end = {"date": parsed_dt.strftime("%Y-%m-%d")}
        else:
            calendar_start = {
                "dateTime": parsed_dt.isoformat(),
                "timeZone": "Asia/Seoul"
            }
            calendar_end = {
                "dateTime": parsed_dt.isoformat(),
                "timeZone": "Asia/Seoul"
            }

        # ✅ 이벤트 객체 구성
        event = {
            "summary": f"[{category}] {title}",
            "start": calendar_start,
            "end": calendar_end,
        }

        if not is_all_day:
            event["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 120},            # 2시간 전
                    {"method": "popup", "minutes": 60 * 24 - 240},  # 하루 전 20시
                ],
            }

        # ✅ 구글 캘린더 일정 등록
        event = calendar_service.events().insert(
            calendarId="primary",
            body=event
        ).execute()

        logger.info(f"✅ Google Calendar 일정 등록 완료 (ID: {event['id']})")

        # ✅ Notion에도 동일 일정 기록
        save_to_notion({
            "title": title,
            "start_date": start_date,
            "category": category,
            "intent": "register_schedule",
            "origin_title": title,
            "origin_date": start_date
        })

    except Exception as e:
        logger.error(
            f"❌ 일정 등록 실패: {str(e)}\n→ title: {title}, date: {start_date}, category: {category}"
        )
        raise
