import os
import logging
from datetime import datetime
from notion_client import Client

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])

def create_notion_page(title: str, date: str, category: str):
    """
    Notion 데이터베이스에 새로운 페이지를 생성합니다.
    
    :param title: 일정 제목
    :param date: 일정 날짜 (YYYY-MM-DD 형식)
    :param category: 일정 카테고리 (Notion select 옵션과 일치해야 함)
    """
    try:
        # ✅ 날짜 형식 검증 (예: 2025-05-17)
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"❌ 날짜 형식 오류: {date} → 'YYYY-MM-DD' 형식이어야 합니다.")

        # ✅ Notion 페이지 생성 요청
        new_page = {
            "parent": {"database_id": os.environ["NOTION_DATABASE_ID"]},
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
                "Date": {"date": {"start": date}},
                "Category": {"select": {"name": category}},  # ❗ 사전에 Notion DB에서 정의된 값이어야 함
            },
        }

        notion.pages.create(
            parent=new_page["parent"],
            properties=new_page["properties"]
        )

        logger.info(f"✅ Notion 페이지가 생성되었습니다. (제목: {title}, 날짜: {date}, 카테고리: {category})")

    except Exception as e:
        # ⚠️ category 오류 가능성까지 함께 로그로 출력
        logger.error(f"❌ Notion 페이지 생성 실패: {str(e)}\n→ category '{category}'가 Notion DB에 정의되어 있는지 확인하세요.")
        raise
