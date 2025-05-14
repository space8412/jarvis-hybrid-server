import os
import logging
from utils import validate_env_variables, APIError, ValidationError, async_api_call, config

logger = logging.getLogger(__name__)

# 환경 변수 검증
validate_env_variables({
    "NOTION_API_KEY": "Notion API key is required",
    "NOTION_DATABASE_ID": "Notion database ID is required"
})

NOTION_TOKEN = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID").strip('"')

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": config.notion_api_version
}

async def save_to_notion(data: dict) -> dict:
    """Notion에 새 페이지 생성"""
    logger.info(f"Attempting to save to Notion: {data}")
    
    if not isinstance(data, dict):
        raise ValidationError("data must be a dictionary")

    notion_payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "일정 제목": {
                "title": [{"text": {"content": data.get("title", "무제")}}]
            },
            "날짜": {
                "date": {"start": data.get("date", "")}
            },
            "카테고리": {
                "select": {"name": data.get("category", "미정")}
            }
        }
    }

    try:
        response = await async_api_call(
            "https://api.notion.com/v1/pages",
            headers=headers,
            method="POST",
            json=notion_payload
        )
        
        logger.info("Successfully saved to Notion")
        return {"status": "saved", "notion_url": response.get("url")}

    except Exception as e:
        logger.error(f"Error saving to Notion: {str(e)}")
        raise APIError(f"Notion API error: {str(e)}")

async def search_notion_page(title: str, date: str) -> str:
    """Notion DB에서 title과 date를 기준으로 기존 페이지 ID를 검색"""
    logger.info(f"Searching Notion page - title: {title}, date: {date}")

    query = {
        "filter": {
            "and": [
                {"property": "일정 제목", "rich_text": {"equals": title}},
                {"property": "날짜", "date": {"equals": date}}
            ]
        }
    }

    try:
        response = await async_api_call(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
            headers=headers,
            method="POST",
            json=query
        )
        
        results = response.get("results", [])
        if results:
            return results[0]["id"]
        return None

    except Exception as e:
        logger.error(f"Error searching Notion page: {str(e)}")
        raise APIError(f"Error searching page: {str(e)}")

async def delete_from_notion(data: dict) -> dict:
    """Notion에서 페이지 삭제"""
    page_id = await search_notion_page(data.get("title", ""), data.get("date", ""))
    if not page_id:
        return {"status": "not_found"}

    try:
        await async_api_call(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=headers,
            method="PATCH",
            json={"archived": True}
        )
        
        logger.info(f"Successfully deleted page: {page_id}")
        return {"status": "deleted", "page_id": page_id}

    except Exception as e:
        logger.error(f"Error deleting from Notion: {str(e)}")
        raise APIError(f"Error deleting page: {str(e)}")

async def update_notion_page(data: dict) -> dict:
    """Notion 페이지 업데이트"""
    page_id = await search_notion_page(data.get("origin_title", ""), data.get("origin_date", ""))
    if not page_id:
        return {"status": "not_found"}

    payload = {
        "properties": {
            "일정 제목": {
                "title": [{"text": {"content": data.get("title", "무제")}}]
            },
            "날짜": {
                "date": {"start": data.get("date", "")}
            },
            "카테고리": {
                "select": {"name": data.get("category", "미정")}
            }
        }
    }

    try:
        await async_api_call(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=headers,
            method="PATCH",
            json=payload
        )
        
        logger.info(f"Successfully updated page: {page_id}")
        return {"status": "updated", "page_id": page_id}

    except Exception as e:
        logger.error(f"Error updating Notion page: {str(e)}")
        raise APIError(f"Error updating page: {str(e)}")
