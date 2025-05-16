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
    try:
        date_iso = ensure_kst_timezone(date)

        # ✅ 제목이 같은 항목만 필터링 (수동 중복 검사)
        query = notion.databases.query(
            database_id=database_id,
            filter={
                "property": "일정 제목",
                "rich_text": {"equals": title}
            }
        )

        for result in query.get("results", []):
            prop = result["properties"]
            d = prop.get("날짜", {}).get("date", {})
            start = d.get("start")
            cat = prop.get("유형", {}).get("select", {}).get("name", "")

            if start == date_iso and cat == category:
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
                "property": "일정 제목",
                "rich_text": {"equals": title}
            }
        )

        deleted = False
        for result in query.get("results", []):
            prop = result["properties"]
            d = prop.get("날짜", {}).get("date", {})
            start = d.get("start")
            cat = prop.get("유형", {}).get("select", {}).get("name", "")

            if start == date_iso and cat == category:
                notion.pages.update(result["id"], archived=True)
                deleted = True

        if deleted:
            return f"✅ Notion 일정 삭제 완료: {title} ({date_iso})"
        else:
            return f"❌ Notion에서 해당 일정을 찾을 수 없습니다: {title}, {date_iso}, {category}"

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
                "property": "일정 제목",
                "rich_text": {"equals": origin_title}
            }
        )

        updated = False
        for result in query.get("results", []):
            prop = result["properties"]
            d = prop.get("날짜", {}).get("date", {})
            start = d.get("start")
            cat = prop.get("유형", {}).get("select", {}).get("name", "")

            if start == date_old and cat == category:
                notion.pages.update(
                    result["id"],
                    properties={
                        "날짜": {"date": {"start": date_new}}
                    }
                )
                updated = True

        if updated:
            return f"✅ Notion 일정 수정 완료: {origin_title} → {date_new}"
        else:
            return f"❌ Notion에서 수정 대상 일정을 찾을 수 없습니다: {origin_title}, {date_old}, {category}"

    except Exception as e:
        logger.error(f"❌ Notion 일정 수정 오류: {str(e)}")
        raise
