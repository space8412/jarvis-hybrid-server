import os
import logging
import re
from notion_client import Client
from dateutil import parser
from datetime import datetime

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

# ✅ 제목 정규화 함수
def normalize_title(title: str) -> str:
    return re.sub(r"\s+", "", title.lower().strip().replace("[", "").replace("]", ""))

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

        # ✅ Notion에서 날짜 범위로 먼저 필터
        query = {
            "filter": {
                "and": [
                    {
                        "property": "날짜",
                        "date": {
                            "on_or_after": start_of_day.isoformat(),
                            "on_or_before": end_of_day.isoformat()
                        }
                    }
                ]
            }
        }

        result = notion.databases.query(database_id=database_id, **query)
        results = result.get("results", [])
        if not results:
            return {"status": "not_found", "message": f"일정 찾을 수 없음: {origin_title} ({origin_date.isoformat()})"}

        # ✅ 유사 제목 탐색
        expected_variants = [
            origin_title,
            f"[{category}] {origin_title}",
            f"{origin_title} ({category})",
            f"{origin_title} - {category}"
        ]
        expected_variants = [normalize_title(v) for v in expected_variants]

        target_pages = []
        for page in results:
            title_prop = page["properties"].get("일정 제목", {}).get("title", [])
            if not title_prop:
                continue
            actual_title = title_prop[0]["plain_text"]
            if any(variant in normalize_title(actual_title) for variant in expected_variants):
                target_pages.append(page)

        if not target_pages:
            return {"status": "not_found", "message": f"제목 조건에 맞는 일정 없음: {origin_title}"}

        # ✅ 일정 수정
        new_date = parser.parse(new_start)
        has_time = new_date.hour != 0 or new_date.minute != 0 or new_date.second != 0
        start_iso = new_date.isoformat()

        for page in target_pages:
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
        return {"status": "success", "updated": len(target_pages)}

    except Exception as e:
        logger.error(f"Notion 수정 오류: {e}")
        return {"status": "error", "message": str(e)}
