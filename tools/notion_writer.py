import os
import logging
from datetime import datetime
from notion_client import Client

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

# ✅ 일정 등록
def create_notion_page(title: str, date: str, category: str):
    """
    Notion 데이터베이스에 새로운 페이지를 생성합니다.
    중복 일정(title + date + category)이 있으면 생략합니다.
    """
    try:
        date_only = date[:10]
        datetime.strptime(date_only, "%Y-%m-%d")

        # 중복 확인
        query = notion.databases.query(
            database_id=database_id,
            filter={
                "and": [
                    {"property": "일정 제목", "rich_text": {"equals": title}},
                    {"property": "날짜", "date": {"equals": date_only}},
                    {"property": "유형", "select": {"equals": category}},
                ]
            }
        )

        if query.get("results"):
            logger.info(f"⚠️ 이미 등록된 일정입니다. (제목: {title}, 날짜: {date_only}, 카테고리: {category}) → 등록 생략")
            return

        # 생성
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "일정 제목": {"title": [{"text": {"content": title}}]},
                "날짜": {"date": {"start": date_only}},
                "유형": {"select": {"name": category}},
            }
        )
        logger.info(f"✅ Notion 페이지가 생성되었습니다. (제목: {title}, 날짜: {date_only}, 카테고리: {category})")

    except Exception as e:
        logger.error(f"❌ Notion 페이지 생성 실패: {str(e)}\n→ category '{category}'가 Notion DB에 정의되어 있는지 확인하세요.")
        raise

# ✅ 일정 삭제
def delete_from_notion(title: str, date: str, category: str) -> str:
    """
    title, date, category가 일치하는 페이지를 찾아 삭제합니다.
    """
    try:
        date_only = datetime.fromisoformat(date).date().isoformat()

        query = notion.databases.query(
            database_id=database_id,
            filter={
                "and": [
                    {"property": "일정 제목", "rich_text": {"equals": title}},
                    {"property": "날짜", "date": {"equals": date_only}},
                    {"property": "유형", "select": {"equals": category}},
                ]
            }
        )

        results = query.get("results", [])
        if not results:
            return f"❌ Notion에서 해당 일정을 찾을 수 없습니다: {title}, {date_only}, {category}"

        for page in results:
            notion.pages.update(page["id"], archived=True)

        return f"✅ Notion 일정 삭제 완료: {title} ({date_only})"

    except Exception as e:
        logger.error(f"❌ Notion 일정 삭제 오류: {str(e)}")
        raise

# ✅ 일정 수정
def update_notion_schedule(origin_title: str, origin_date: str, new_date: str, category: str) -> str:
    """
    title + date + category로 기존 일정을 찾아 날짜를 새로 갱신합니다.
    """
    try:
        date_old = datetime.fromisoformat(origin_date).date().isoformat()
        date_new = datetime.fromisoformat(new_date).date().isoformat()

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
            return f"❌ Notion에서 수정 대상 일정을 찾을 수 없습니다."

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
