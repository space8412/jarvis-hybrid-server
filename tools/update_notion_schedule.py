import os
import logging
from notion_client import Client
from dateutil import parser
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

def update_notion_schedule(parsed_data: dict) -> dict:
    try:
        origin_title = parsed_data.get("origin_title")
        origin_date_str = parsed_data.get("origin_date")
        new_title = parsed_data.get("title")
        new_start = parsed_data.get("start_date")
        category = parsed_data.get("category", "기타")

        if not origin_title or not origin_date_str:
            raise ValueError("❌ origin_title 또는 origin_date 누락")

        origin_date = parser.parse(origin_date_str)
        start_of_day = origin_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = origin_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        query = {
            "and": [
                {
                    "property": "일정 제목",
                    "title": {"contains": origin_title}
                },
                {
                    "property": "날짜",
                    "date": {
                        "on_or_after": start_of_day.isoformat(),
                        "on_or_before": end_of_day.isoformat()
                    }
                }
            ]
        }

        result = notion.databases.query(database_id=database_id, filter=query)
        results = result.get("results", [])
        if not results:
            return {"status": "not_found", "message": f"일정 찾을 수 없음: {origin_title} ({origin_date.isoformat()})"}

        new_date = parser.parse(new_start)
        has_time = new_date.hour != 0 or new_date.minute != 0 or new_date.second != 0
        start_iso = new_date.isoformat()

        for page in results:
            page_id = page["id"]
            properties = {
                "일정 제목": {"title": [{"text": {"content": new_title[:100]}}]},
                "날짜": {
                    "date": {
                        "start": start_iso,
                        "time_zone": "Asia/Seoul" if has_time else None
                    }
                },
                "유형": {"select": {"name": category}}
            }
            notion.pages.update(page_id=page_id, properties=properties)

        logger.info(f"✏️ Notion 일정 수정 완료: {new_title}")
        return {"status": "success", "updated": len(results)}

    except Exception as e:
        logger.error(f"Notion 수정 오류: {e}")
        return {"status": "error", "message": str(e)}
