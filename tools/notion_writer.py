import os
import logging
from datetime import datetime
from notion_client import Client
from dateutil import parser
from tools.utils import normalize_notion_date  # ✅ 날짜 포맷 정제 함수 임포트

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]


def save_to_notion(parsed_data: dict) -> dict:
    try:
        title = parsed_data.get("title")
        date_str = parsed_data.get("start_date") or parsed_data.get("date")
        category = parsed_data.get("category") or "기타"

        if not title or not date_str:
            raise ValueError("❌ title 또는 start_date 누락")

        # ✅ 날짜 포맷 정제
        notion_date = normalize_notion_date(date_str)

        properties = {
            "일정 제목": {"title": [{"text": {"content": title[:100]}}]},
            "날짜": {
                "date": notion_date
            },
            "유형": {"select": {"name": category}}
        }

        notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        logger.info(f"✅ Notion 등록 성공: {title}")
        return {"status": "success", "title": title, "start": date_str, "category": category}

    except Exception as e:
        logger.error(f"Notion 등록 오류: {e}")
        return {"status": "error", "message": str(e)}


def delete_from_notion(parsed_data: dict) -> dict:
    try:
        title = parsed_data.get("origin_title") or parsed_data.get("title")
        date_str = parsed_data.get("origin_date") or parsed_data.get("start_date") or parsed_data.get("date")

        if not title or not date_str:
            raise ValueError("❌ 삭제를 위해 title과 date가 필요합니다.")

        date = parser.parse(date_str) if isinstance(date_str, str) else date_str
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        query = {
            "and": [
                {
                    "property": "일정 제목",
                    "title": {"equals": title}
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
            return {"status": "not_found", "message": f"일정 찾을 수 없음: {title} ({date.isoformat()})"}

        for page in results:
            notion.pages.update(page["id"], archived=True)

        logger.info(f"🗑️ Notion 정확 삭제 완료: {title}")
        return {"status": "success", "deleted": len(results)}

    except Exception as e:
        logger.error(f"Notion 삭제 오류: {e}")
        return {"status": "error", "message": str(e)}


def update_notion_schedule(parsed_data: dict) -> dict:
    try:
        delete_result = delete_from_notion(parsed_data)
        if delete_result.get("status") != "success":
            return {"status": "delete_failed", "detail": delete_result}

        save_result = save_to_notion(parsed_data)
        return {"status": "updated", "detail": save_result}

    except Exception as e:
        logger.error(f"Notion 수정 오류: {e}")
        return {"status": "error", "message": str(e)}
