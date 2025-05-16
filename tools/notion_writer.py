import os
from notion_client import Client
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ✅ Notion 클라이언트 초기화
notion = Client(auth=os.environ["NOTION_TOKEN"])

def save_to_notion(parsed_data: dict) -> dict:
    """
    파싱된 데이터를 Notion에 저장합니다.
    :param parsed_data: title, date, category가 포함된 dict
    :return: 저장 결과 dict (성공/실패 포함)
    """
    try:
        title = parsed_data.get("title")
        date = parsed_data.get("date")
        category = parsed_data.get("category", "기타")
        origin_title = parsed_data.get("origin_title")
        origin_date = parsed_data.get("origin_date")

        # ✅ 필수 항목 확인
        if not title or not date:
            raise ValueError("❌ title 또는 date가 누락되었습니다.")

        if not isinstance(date, datetime):
            raise ValueError("❌ date는 datetime 형식이어야 합니다.")

        # ✅ 시간 포함 여부 판단
        has_time = date.hour != 0 or date.minute != 0 or date.second != 0
        start_str = date.isoformat()

        # ✅ 데이터베이스 ID
        database_id = os.environ["NOTION_DATABASE_ID"]

        # ✅ Notion에 페이지 생성
        response = notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Name": {
                    "title": [{"text": {"content": title}}]
                },
                "Date": {
                    "date": {
                        "start": start_str,
                        "time_zone": "Asia/Seoul" if has_time else None
                    }
                },
                "Category": {
                    "select": {"name": category}
                },
                # 선택: 원본 정보도 함께 기록 (확장 가능)
                "origin_title": {
                    "rich_text": [{"text": {"content": origin_title}}]
                } if origin_title else {},
                "origin_date": {
                    "rich_text": [{"text": {"content": str(origin_date)}}]
                } if origin_date else {}
            }
        )

        logger.info(f"✅ Notion 등록 성공: {title}")
        return {
            "status": "success",
            "title": title,
            "start": start_str,
            "category": category
        }

    except Exception as e:
        error_msg = f"Notion 등록 오류: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
