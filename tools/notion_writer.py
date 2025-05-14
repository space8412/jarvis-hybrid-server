import os
import requests

# ✅ 환경변수 불러오기 및 정리 (따옴표 제거 포함)
NOTION_TOKEN = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID").strip('"')

# ✅ 공통 헤더
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ✅ Notion에 일정 등록
def save_to_notion(data: dict) -> dict:
    notion_payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "일정 제목": {  # ← 실제 Notion 필드명에 맞게 수정됨
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


# ✅ 기존 일정 검색 (제목+날짜)
def search_notion_page(title: str, date: str) -> str:
    query = {
        "filter": {
            "and": [
                {"property": "일정 제목", "rich_text": {"contains": title}},
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


# ✅ 일정 삭제 (archive 처리)
def delete_from_notion(data: dict) -> dict:
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


# ✅ 일정 수정 (기존 제목+날짜 기준으로 찾아서 업데이트)
def update_notion_page(data: dict) -> dict:
    page_id = search_notion_page(data.get("origin_title", ""), data.get("origin_date", ""))
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

    response = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=headers,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(f"수정 실패: {response.text}")

    return {"status": "updated", "page_id": page_id}
