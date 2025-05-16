import os
import logging
from datetime import datetime
from notion_client import Client

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

# ✅ 타임존 보정 함수 (+09:00 붙이기)
def ensure_kst_timezone(date_str: str) -> str:
    if "T" in date_str and "+" not in date_str:
        return date_str + "+09:00"
    return date_str

# ✅ 일정 등록
def create_notion_page(title: str, date: str, category: str):
    try:
        date = ensure_kst_timezone(date)
        date_iso = datetime.fromisoformat(date).isoformat()

        # 중복 확인
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

        # 생성
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "일정 제목": {"title": [{"text": {"content": title}}]},
                "날짜": {"date": {"start": date_iso}},
                "유형": {"select": {"name": category}},
            }
        )
        logger.info(f"✅ Notion 페이지 생성 완료 (제목: {title}, 날짜: {date_iso}, 카테고리: {category})")

    except Exception as e:
        logger.error(f"❌ Notion 페이지 생성 실패: {str(e)}")
        raise

# ✅ 일정 삭제
def delete_from_notion(title: str, date: str, category: str) -> str:
    try:
        date = ensure_kst_timezone(date)
        date_iso = datetime.fromisoformat(date).isoformat()

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
        origin_date = ensure_kst_timezone(origin_date)
        new_date = ensure_kst_timezone(new_date)
        origin_iso = datetime.fromisoformat(origin_date).isoformat()
        new_iso = datetime.fromisoformat(new_date).isoformat()

        query = notion.databases.query(
            database_id=database_id,
            filter={
                "and": [
                    {"property": "일정 제목", "rich_text": {"equals": origin_title}},
                    {"property": "날짜", "date": {"equals": origin_iso}},
                    {"property": "유형", "select": {"equals": category}},
                ]
            }
        )

        results = query.get("results", [])
        if not results:
            return f"❌ Notion에서 수정 대상 일정을 찾을 수 없습니다."

        for page in results:
            notion.pages.update(
                page["id"],
                properties={"날짜": {"date": {"start": new_iso}}}
            )

        return f"✅ Notion 일정 수정 완료: {origin_title} → {new_iso}"

    except Exception as e:
        logger.error(f"❌ Notion 일정 수정 오류: {str(e)}")
        raise
