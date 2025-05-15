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

# ✅ 구글 캘린더 서비스 초기화
creds = Credentials.from_authorized_user_info(
    json.loads(creds_json),
    ["https://www.googleapis.com/auth/calendar"]
)
calendar_service = build("calendar", "v3", credentials=creds)

def register_schedule(title: str, start_date: str, category: str):
    """
    제목, 날짜, 카테고리를 받아 구글 캘린더에 일정을 등록하고 Notion에 기록합니다.
    
    :param title: 일정 제목
    :param start_date: 시작 날짜 (YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS 형식)
    :param category: 일정 카테고리 (예: 회의, 콘텐츠, 개인 등)
    """
    try:
        # ✅ 시간 포함 여부 확인
        is_all_day = "T" not in start_date
        calendar_start = {}
        calendar_end = {}

        if is_all_day:
            # 종일 일정 (date만 사용)
            calendar_start["date"] = start_date
            calendar_end["date"] = start_date
        else:
            # 시간 포함 일정 (dateTime 사용)
            calendar_start["dateTime"] = start_date
            calendar_start["timeZone"] = "Asia/Seoul"
            calendar_end["dateTime"] = start_date
            calendar_end["timeZone"] = "Asia/Seoul"

        # ✅ 이벤트 객체 구성
        event = {
            "summary": f"[{category}] {title}",
            "start": calendar_start,
            "end": calendar_end,
        }

        # ✅ 시간 포함 일정에만 알림 설정
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
        notion_date = start_date.split("T")[0]  # 시간 포함 일정에서도 YYYY-MM-DD 추출
        create_notion_page(title, notion_date, category)

    except Exception as e:
        logger.error(
            f"❌ 일정 등록 실패: {str(e)}\n→ title: {title}, date: {start_date}, category: {category}"
        )
        raise
