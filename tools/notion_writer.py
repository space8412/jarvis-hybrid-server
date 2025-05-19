import os
import logging
from datetime import datetime
from notion_client import Client

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]


def save_to_notion(parsed_data: dict) -> dict:
    try:
        title = parsed_data.get("title")
        date = parsed_data.get("start_date") or parsed_data.get("date")
        category = parsed_data.get("category", "기타")
        origin_title = parsed_data.get("origin_title")
        origin_date = parsed_data.get("origin_date")

        if not title or not date:
            raise ValueError("❌ title 또는 date 누락")

        if not isinstance(date, datetime):
            from dateutil import parser
            try:
                date = parser.parse(date)
            except Exception as e:
                raise ValueError(f"❌ 날짜 파싱 실패: {e}")

        has_time = date.hour != 0 or date.minute != 0 or date.second != 0
        start_str = date.isoformat()

        properties = {
            "일정 제목": {"title": [{"text": {"content": title}}]},
            "날짜": {
                "date": {
                    "start": start_str,
                    "time_zone": "Asia/Seoul" if has_time else None
                }
            },
            "유형": {"select": {"name": category}}
        }

        if origin_title:
            properties["origin_title"] = {"rich_text": [{"text": {"content": origin_title}}]}
        if origin_date:
            properties["origin_date"] = {"rich_text": [{"text": {"content": str(origin_date)}}]}

        response = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        logger.info(f"✅ Notion 등록 성공: {title}")
        return {"status": "success", "title": title, "start": start_str, "category": category}

    except Exception as e:
        logger.error(f"Notion 등록 오류: {e}")
        return {"status": "error", "message": str(e)}


def delete_from_notion(parsed_data: dict) -> dict:
    try:
        title = parsed_data.get("origin_title") or parsed_data.get("title")
        date = parsed_data.get("origin_date") or parsed_data.get("start_date") or parsed_data.get("date")

        if not title or not date:
            raise ValueError("❌ 삭제를 위해 title과 date가 필요합니다.")

        if not isinstance(date, datetime):
            from dateutil import parser
            try:
                date = parser.parse(date)
            except Exception as e:
                raise ValueError(f"❌ 날짜 파싱 실패: {e}")

        date_str = date.isoformat()

        # ✅ 범위 조건으로 시간 포함된 일정도 삭제 가능하게 변경
        result = notion.databases.query(
            database_id=database_id,
            filter={
                "and": [
                    {
                        "property": "일정 제목",
                        "title": {
                            "equals": title
                        }
                    },
                    {
                        "property": "날짜",
                        "date": {
                            "on_or_after": date_str,
                            "on_or_before": date_str
                        }
                    }
                ]
            }
        )

        results = result.get("results", [])
        if not results:
            logger.warning(f"🛑 삭제 대상 없음: 제목={title}, 날짜={date_str}")
            return {"status": "not_found", "message": f"일정 찾을 수 없음: {title} - {date_str}"}

        for page in results:
            notion.pages.update(page["id"], archived=True)

        logger.info(f"🗑️ Notion 정확 삭제 완료: {title}")
        return {"status": "success", "deleted": len(results)}

    except Exception as e:
        logger.error(f"Notion 삭제 오류: {e}")
        return {"status": "error", "message": str(e)}


def update_notion_schedule(parsed_data: dict) -> dict:
    """
    기존 일정 삭제 후, 새로운 일정 등록 (수정 처리)
    """
    try:
        delete_result = delete_from_notion(parsed_data)
        if delete_result.get("status") != "success":
            return {"status": "delete_failed", "detail": delete_result}

        save_result = save_to_notion(parsed_data)
        return {"status": "updated", "detail": save_result}

    except Exception as e:
        logger.error(f"Notion 수정 오류: {e}")
