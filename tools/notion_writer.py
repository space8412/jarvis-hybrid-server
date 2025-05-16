import os
from notion_client import Client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

notion = Client(auth=os.environ["NOTION_TOKEN"])
database_id = os.environ["NOTION_DATABASE_ID"]

# ✅ 일정 저장
def save_to_notion(data: dict) -> dict:
    title = data["title"]
    date_str = data["start_date"]
    category = data["category"]

    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        raise Exception(f"날짜 변환 실패: {date_str}")

    # ✅ 기존 일정 확인
    response = notion.databases.query(
        **{
            "database_id": database_id,
            "filter": {
                "and": [
                    {"property": "Name", "title": {"equals": title}},
                    {"property": "Date", "date": {"on_or_after": date.isoformat()}},
                    {"property": "Category", "select": {"equals": category}},
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

    # ✅ 새 일정 등록
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


# ✅ 일정 삭제
def delete_from_notion(title: str, date_str: str, category: str) -> str:
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
                    {"property": "Category", "select": {"equals": category}},
                ]
            }
        }
    )

    deleted = 0
    for page in response.get("results", []):
        page_id = page["id"]
        notion.pages.update(page_id=page_id, archived=True)
        deleted += 1

    if deleted == 0:
        logger.warning(f"⚠️ Notion에서 삭제 대상 없음: {title}, {date_str}, {category}")
        return "Notion에서 삭제 대상 없음"
    else:
        logger.info(f"🗑️ Notion 일정 삭제 완료 ({deleted}건)")
        return f"Notion에서 {deleted}건 삭제됨"
