import os
import logging
from notion_client import Client

logger = logging.getLogger(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])

def create_notion_page(title: str, date: str, category: str):
    """
    Notion 데이터베이스에 새로운 페이지를 생성합니다.
    
    :param title: 일정 제목
    :param date: 일정 날짜 (YYYY-MM-DD 형식)
    :param category: 일정 카테고리
    """
    try:
        new_page = {
            "parent": {"database_id": os.environ["NOTION_DATABASE_ID"]},
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
                "Date": {"date": {"start": date}},
                "Category": {"select": {"name": category}},
            },
        }
        notion.pages.create(parent=new_page["parent"], properties=new_page["properties"])
        logger.info(f"Notion 페이지가 생성되었습니다. (제목: {title})")
    except Exception as e:
        logger.error(f"Notion 페이지 생성 중 오류 발생: {str(e)}")
        raise