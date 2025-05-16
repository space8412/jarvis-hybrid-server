import os
import logging
from datetime import datetime, timezone, timedelta
from notion_client import Client

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

# ✅ 한국 시간 보정
def ensure_kst_timezone(date_str: str) -> str:
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))  # KST
        return dt.isoformat()
    except Exception:
        raise ValueError(f"❌ 잘못된 ISO 날짜 형식: {date_str}")

# ✅ 일정 등록
def create_notion_page(title: str, date: str, category: str):
    """
    Notion 데이터베이스에 새로운 페이지를 생성합니다.
    중복 일정(title + full datetime + category)이 있으면 생략합니다.
    """
    try:
        date_iso = ensure_kst_timezone(date)

        query = notion.databases.query(
            database_id=database_id,
            filter={
                "and": [
                    {"property": "일정 제목", "rich_text": {"equals": title}},
                    {"property": "날짜", "date": {"equals": date_iso}},
                    {"property": "유형", "select": {"equals": category}},
                ]
            }
        )

        if query.get("results"):
            logger.info(f"⚠️ 이미 등록된 일정입니다. (제목: {title}, 날짜: {date_iso}, 카테고리: {category}) → 등록 생략")
            return

        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "일정 제목": {"title": [{"text": {"content": title}}]},
                "날짜": {"date": {"start": date_iso}},
                "유형": {"select": {"name": category}},
            }
        )
        logger.info(f"✅ Notion 페이지가 생성되었습니다. (제목: {title}, 날짜: {date_iso}, 카테고리: {category})")

    except Exception as e:
        logger.error(f"❌ Notion 페이지 생성 실패: {str(e)}")
        raise

# ✅ 일정 삭제
def delete_from_notion(title: str, date: str, category: str) -> str:
    try:
        date_iso = ensure_kst_timezone(date)

        query = notion.databases.query(
            database_id=database_id,
            filter={
                "and": [
                    {"property": "일정 제목", "rich_text": {"equals": title}},
                    {"property": "날짜", "date": {"equals": date_iso}},
                    {"property": "유형", "select": {"equals": category}},
                ]
            }
        )

        results = query.get("results", [])
        if not results:
            return f"❌ Notion에서 해당 일정을 찾을 수 없습니다: {title}, {date_iso}, {category}"

        for page in results:
            notion.pages.update(page["id"], archived=True)

        return f"✅ Notion 일정 삭제 완료: {title} ({date_iso})"

    except Exception as e:
        logger.error(f"❌ Notion 일정 삭제 오류: {str(e)}")
        raise

# ✅ 일정 수정
def update_notion_schedule(origin_title: str, origin_date: str, new_date: str, category: str) -> str:
    try:
        date_old = ensure_kst_timezone(origin_date)
        date_new = ensure_kst_timezone(new_date)

        query = notion.databases.query(
            database_id=database_id,
            filter={
                "and": [
                    {"property": "일정 제목", "rich_text": {"equals": origin_title}},
                    {"property": "날짜", "date": {"equals": date_old}},
                    {"property": "유형", "select": {"equals": category}},
                ]
            }
        )

        results = query.get("results", [])
        if not results:
            return f"❌ Notion에서 수정 대상 일정을 찾을 수 없습니다: {origin_title}, {date_old}"

        for page in results:
            notion.pages.update(
                page["id"],
                properties={
                    "날짜": {"date": {"start": date_new}}
                }
            )

        return f"✅ Notion 일정 수정 완료: {origin_title} → {date_new}"

    except Exception as e:
        logger.error(f"❌ Notion 일정 수정 오류: {str(e)}")
        raise
