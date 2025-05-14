import requests
import os
import logging

logger = logging.getLogger("tools.verify_database")

NOTION_API_URL = "https://api.notion.com/v1/databases/"
NOTION_API_VERSION = "2022-06-28"
NOTION_TOKEN = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")


def get_notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }


class DatabaseVerifier:
    def verify_and_fix_database(self):
        try:
            logger.info("Verifying Notion database structure...")
            url = f"{NOTION_API_URL}{DATABASE_ID}"
            headers = get_notion_headers()
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                logger.error(f"Error verifying database: {response.text}")
                return False

            data = response.json()
            properties = data.get("properties", {})

            required_properties = {
                "Name": {"type": "title", "title": {}},
                "Tags": {"type": "multi_select", "multi_select": {}},
                "Status": {"type": "select", "select": {}},
                "Priority": {"type": "select", "select": {}},
                "Due Date": {"type": "date", "date": {}},
            }

            for name, schema in required_properties.items():
                if schema["type"] == "title":
                    title_exists = any(prop.get("type") == "title" for prop in properties.values())
                    if title_exists:
                        logger.info("Title property already exists. Skipping creation.")
                        continue

                if name not in properties:
                    logger.info(f"Creating missing property: {name}")
                    patch_response = requests.patch(
                        url,
                        headers=headers,
                        json={"properties": {name: schema}}
                    )

                    if patch_response.status_code != 200:
                        logger.error(f"Failed to create property '{name}': {patch_response.text}")

            logger.info("Database verification complete.")
            return True

        except Exception as e:
            logger.error(f"Exception during database verification: {e}")
            return False
