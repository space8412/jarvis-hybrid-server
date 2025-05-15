import os
import json
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ✅ 환경변수로부터 인증 정보 불러오기
creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
creds = Credentials.from_authorized_user_info(json.loads(creds_json), ["https://www.googleapis.com/auth/calendar"])
calendar_service = build("calendar", "v3", credentials=creds)

def delete_schedule(start_date: str):
    """
    시작 날짜를 받아 해당 날짜의 모든 일정을 삭제합니다.
    
    :param start_date: 삭제할 일정 날짜 (e.g. "5월 17일") 
    """
    try:
        start_date_obj = datetime.strptime(start_date, "%m월 %d일")
        start_date_str = start_date_obj.strftime("%Y-%m-%d")
        end_date_str = start_date_obj.strftime("%Y-%m-%d")

        events_result = calendar_service.events().list(
            calendarId="primary",
            timeMin=start_date_str + "T00:00:00Z",
            timeMax=end_date_str + "T23:59:59Z",
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])

        for event in events:
            calendar_service.events().delete(calendarId="primary", eventId=event["id"]).execute()

        print(f"{start_date} 일정들이 삭제되었습니다. (총 {len(events)}개)")
    except Exception as e:
        print(f"일정 삭제 중 오류 발생: {e}")
