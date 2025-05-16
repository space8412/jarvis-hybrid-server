import os
import logging
from datetime import datetime
from notion_client import Client

logger = logging.getLogger(__name__)

notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]


def save_to_notion(data: dict) -> dict:
    title = data["title"]
    date_str = data["start_date"]
    category = data["category"]

    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        raise Exception(f"날짜 변환 실패: {date_str}")

    response = notion.databases.query(
        **{
            "database_id": database_id,
            "filter": {
                "and": [
                    {"property": "Name", "title": {"equals": title}},
                    {"property": "Date", "date": {"on_or_after": date.isoformat()}},
                    {"property": "Category", "select": {"equals": category}}
                ]
            }
        }
    )

    for result in response.get("results", []):
        properties = result["properties"]
        existing_title = properties["Name"]["title"][0]["plain_text"]
        existing_date_str = properties["Date"]["date"]["start"]
        existing_category = properties["Category"]["select"]["name"]

        try:
            existing_date = datetime.fromisoformat(existing_date_str)
        except ValueError:
            continue

        if (
            title == existing_title and
            date.isoformat() == existing_date.isoformat() and
            category == existing_category
        ):
            logger.info(
                f"⚠️ 이미 등록된 일정입니다. (제목: {title}, 날짜: {date.isoformat()}, 카테고리: {category}) → 등록 생략"
            )
            return {"status": "skipped", "message": "이미 등록된 일정입니다."}

    notion.pages.create(
        **{
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
                "Date": {"date": {"start": date.isoformat()}},
                "Category": {"select": {"name": category}},
            }
        }
    )

    logger.info(
        f"✅ Notion 페이지가 생성되었습니다. (제목: {title}, 날짜: {date.isoformat()}, 카테고리: {category})"
    )
    return {"status": "created", "message": "일정이 등록되었습니다."}


def delete_from_notion(title: str, date_str: str, category: str) -> str:
    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        raise Exception(f"날짜 파싱 실패: {date_str}")

    response = notion.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Name", "title": {"equals": title}},
                {"property": "Date", "date": {"on_or_after": date.isoformat()}},
                {"property": "Category", "select": {"equals": category}}
            ]
        }
    )

    results = response.get("results", [])
    if not results:
        return f"📭 삭제 대상 없음: {title} ({date_str})"

    for page in results:
        page_id = page["id"]
        notion.blocks.delete(block_id=page_id)

    return f"🗑️ Notion에서 {len(results)}건 삭제 완료"


def update_notion_schedule(origin_title: str, origin_date: str, new_date: str, category: str):
    try:
        origin_dt = datetime.fromisoformat(origin_date)
        new_dt = datetime.fromisoformat(new_date)
    except Exception as e:
        raise Exception(f"날짜 파싱 실패: {e}")

    response = notion.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Name", "title": {"equals": origin_title}},
                {"property": "Date", "date": {"on_or_after": origin_dt.isoformat()}},
                {"property": "Category", "select": {"equals": category}}
            ]
        }
    )

    results = response.get("results", [])
    if not results:
        logger.warning(f"⚠️ 수정 대상 일정 없음: {origin_title} ({origin_date})")
        return

    for page in results:
        page_id = page["id"]
        notion.pages.update(
            page_id=page_id,
            properties={"Date": {"date": {"start": new_dt.isoformat()}}}
        )

        logger.info(
            f"🔁 Notion 일정 수정 완료: {origin_title} → {new_dt.isoformat()}"
        )
