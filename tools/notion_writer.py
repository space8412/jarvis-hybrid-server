import os
import requests

NOTION_TOKEN = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID").strip('"')

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def save_to_notion(data: dict) -> dict:
    print("✅ save_to_notion 호출됨")
    print(f"📦 받은 데이터: {data}")
    print(f"🧩 DATABASE_ID: {repr(DATABASE_ID)}")

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

    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=notion_payload)

    if response.status_code != 200:
        print("❌ Notion 등록 실패")
        print("📥 요청 내용:", notion_payload)
        print("📤 응답 내용:", response.text)
        raise Exception(f"Notion API 오류: {response.text}")

    print("✅ Notion 등록 성공")
    return {"status": "saved", "notion_url": response.json().get("url")}

def search_notion_page(title: str, date: str) -> str:
    """
    Notion DB에서 title과 date를 기준으로 기존 페이지 ID를 검색
    검색 실패 시 디버깅 로그 출력 포함
    """
    print(f"🔍 검색 요청 - title: {title}, date: {date}")

    query = {
        "filter": {
            "and": [
                {"property": "일정 제목", "rich_text": {"equals": title}},
                {"property": "날짜", "date": {"equals": date}}
            ]
        }
    }

    response = requests.post(
        f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
        headers=headers,
        json=query
    )

    print("📤 Notion 응답 상태코드:", response.status_code)
    try:
        data = response.json()
        print("📄 응답 결과 내용:", data)
        results = data.get("results", [])
        if results:
            return results[0]["id"]
        return None
    except Exception as e:
        print("🚨 JSON 파싱 오류:", str(e))
        return None

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
