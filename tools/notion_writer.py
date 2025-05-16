import os
import logging
from datetime import datetime, timezone, timedelta
from notion_client import Client

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

# ✅ 한국 시간 보정 함수
def ensure_kst_datetime(date_str: str) -> datetime:
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))  # KST
        return dt.astimezone(timezone(timedelta(hours=9)))  # 항상 KST로 통일
    except Exception:
        raise ValueError(f"❌ 잘못된 ISO 날짜 형식: {date_str}")

# ✅ 일정 등록
def create_notion_page(title: str, date: str, category: str):
    try:
        new_dt = ensure_kst_datetime(date)

        query = notion.databases.query(
            database_id=database_id,
            filter={"property": "일정 제목", "rich_text": {"equals": title}}
        )

        for page in query.get("results", []):
            existing_start = page["properties"]["날짜"]["date"].get("start")
            existing_category = page["properties"]["유형"]["select"].get("name")
            if not existing_start:
                continue

            existing_dt = ensure_kst_datetime(existing_start)

            if existing_dt == new_dt and existing_category == category:
                logger.info(f"⚠️ 이미 등록된 일정입니다. (제목: {title}, 날짜: {existing_start}, 카테고리: {category}) → 등록 생략")
                return

        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "일정 제목": {"title": [{"text": {"content": title}}]},
                "날짜": {"date": {"start": new_dt.isoformat()}},
                "유형": {"select": {"name": category}},
            }
        )
        logger.info(f"✅ Notion 페이지가 생성되었습니다. (제목: {title}, 날짜: {new_dt.isoformat()}, 카테고리: {category})")

    except Exception as e:
        logger.error(f"❌ Notion 페이지 생성 실패: {str(e)}")
        raise

# ✅ 일정 삭제
def delete_from_notion(title: str, date: str, category: str) -> str:
    try:
        target_dt = ensure_kst_datetime(date)

        query = notion.databases.query(
            database_id=database_id,
            filter={"property": "일정 제목", "rich_text": {"equals": title}}
        )

        deleted = False
        for page in query.get("results", []):
            existing_start = page["properties"]["날짜"]["date"].get("start")
            existing_category = page["properties"]["유형"]["select"].get("name")
            if not existing_start:
                continue

            existing_dt = ensure_kst_datetime(existing_start)

            if existing_dt == target_dt and existing_category == category:
                notion.pages.update(page["id"], archived=True)
                deleted = True

        if deleted:
            return f"✅ Notion 일정 삭제 완료: {title} ({target_dt.isoformat()})"
        else:
            return f"❌ Notion에서 해당 일정을 찾을 수 없습니다: {title}, {target_dt.isoformat()}, {category}"

    except Exception as e:
        logger.error(f"❌ Notion 일정 삭제 오류: {str(e)}")
        raise

# ✅ 일정 수정
def update_notion_schedule(origin_title: str, origin_date: str, new_date: str, category: str) -> str:
    try:
        old_dt = ensure_kst_datetime(origin_date)
        new_dt = ensure_kst_datetime(new_date)

        query = notion.databases.query(
            database_id=database_id,
            filter={"property": "일정 제목", "rich_text": {"equals": origin_title}}
        )

        updated = False
        for page in query.get("results", []):
            existing_start = page["properties"]["날짜"]["date"].get("start")
            existing_category = page["properties"]["유형"]["select"].get("name")
            if not existing_start:
                continue

            existing_dt = ensure_kst_datetime(existing_start)

            if existing_dt == old_dt and existing_category == category:
                notion.pages.update(
                    page["id"],
                    properties={"날짜": {"date": {"start": new_dt.isoformat()}}}
                )
                updated = True

        if updated:
            return f"✅ Notion 일정 수정 완료: {origin_title} → {new_dt.isoformat()}"
        else:
            return f"❌ Notion에서 수정 대상 일정을 찾을 수 없습니다: {origin_title}, {old_dt.isoformat()}"

    except Exception as e:
        logger.error(f"❌ Notion 일정 수정 오류: {str(e)}")
        raise
