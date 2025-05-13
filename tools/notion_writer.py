import os
import requests

NOTION_TOKEN = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def save_to_notion(data: dict) -> dict:
    notion_payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "제목": {
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

    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=notion_payload
    )

    if response.status_code != 200:
        raise Exception(f"Notion API 오류: {response.text}")

    return {"status": "saved", "notion_url": response.json().get("url")}

def delete_from_notion(data: dict) -> dict:
    # ⚠️ 실제로는 DB에서 검색하여 해당 ID를 찾고 삭제해야 함 (여기선 mock)
    return {"status": "deleted (mock)", "title": data.get("title")}

def update_notion_page(data: dict) -> dict:
    # ⚠️ 실제로는 ID 검색 후 patch 요청해야 함 (여기선 mock)
    return {
        "status": "updated (mock)",
        "origin_title": data.get("origin_title"),
        "title": data.get("title")
    }
