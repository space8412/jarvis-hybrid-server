import os
import logging
from datetime import datetime
from notion_client import Client

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])

def create_notion_page(title: str, date: str, category: str):
    """
    Notion 데이터베이스에 새로운 페이지를 생성합니다.
    중복 일정(title + date + category)이 있으면 생략합니다.
    """
    try:
        # ✅ ISO 형식 → YYYY-MM-DD 로 보정
        try:
            date_only = date[:10]  # 예: 2025-05-18T14:00:00 → 2025-05-18
            datetime.strptime(date_only, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"❌ 날짜 형식 오류: {date} → 'YYYY-MM-DD' 형식이어야 합니다.")

        # ✅ 중복 일정 확인
        query = notion.databases.query(
            database_id=os.environ["NOTION_DATABASE_ID"],
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

        # ✅ Notion 페이지 생성 요청
        new_page = {
            "parent": {"database_id": os.environ["NOTION_DATABASE_ID"]},
            "properties": {
                "일정 제목": {"title": [{"text": {"content": title}}]},
                "날짜": {"date": {"start": date_only}},
                "유형": {"select": {"name": category}},
            },
        }

        notion.pages.create(
            parent=new_page["parent"],
            properties=new_page["properties"]
        )

        logger.info(f"✅ Notion 페이지가 생성되었습니다. (제목: {title}, 날짜: {date_only}, 카테고리: {category})")

    except Exception as e:
        logger.error(f"❌ Notion 페이지 생성 실패: {str(e)}\n→ category '{category}'가 Notion DB에 정의되어 있는지 확인하세요.")
        raise
