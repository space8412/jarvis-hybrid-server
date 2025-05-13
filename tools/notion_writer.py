import os
import requests

# ✅ Notion API Key 및 Database ID 환경변수 불러오기
NOTION_TOKEN = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# ✅ 공통 요청 헤더 설정
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def save_to_notion(data: dict) -> dict:
    """일정 데이터를 Notion DB에 새 페이지로 저장"""
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

    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=notion_payload)
    if response.status_code != 200:
        raise Exception(f"Notion API 오류: {response.text}")

    return {"status": "saved", "notion_url": response.json().get("url")}

def search_notion_page(title: str, date: str) -> str:
    """제목과 날짜 기준으로 기존 페이지 ID를 검색"""
    query = {
        "filter": {
            "and": [
                {"property": "제목", "rich_text": {"contains": title}},
                {"property": "날짜", "date": {"equals": date}}
            ]
        }
    }
    response = requests.post(
        f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
        headers=headers,
        json=query
    )
    results = response.json().get("results", [])
    if results:
        return results[0]["id"]
    return None

def delete_from_notion(data: dict) -> dict:
    """기존 일정을 찾아 Notion에서 삭제 (archive 처리)"""
    page_id = search_notion_page(data.get("title", ""), data.get("date", ""))
    if not page_id:
        return {"status": "not_found"}

    response = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=headers,
        json={"archived": True}
    )
    if response.status_code != 200:
        raise Exception(f"삭제 실패: {response.text}")

    return {"status": "deleted", "page_id": page_id}

def update_notion_page(data: dict) -> dict:
    """기존 일정을 찾아 제목/날짜/카테고리를 수정"""
    page_id = search_notion_page(data.get("origin_title", ""), data.get("origin_date", ""))
    if not page_id:
        return {"status": "not_found"}

    payload = {
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

    response = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=headers,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(f"수정 실패: {response.text}")

    return {"status": "updated", "page_id": page_id}
