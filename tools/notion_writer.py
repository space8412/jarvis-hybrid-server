from notion_client import Client
from config import NOTION_API_KEY, NOTION_DATABASE_ID
from utils import get_logger

logger = get_logger(__name__)

class NotionWriter:
    def __init__(self):
        self.client = Client(auth=NOTION_API_KEY)
        self.database_id = NOTION_DATABASE_ID

    def create_page(self, title, content, tags=None):
        """Create a new page in the Notion database"""
        try:
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }

            if tags:
                properties["Tags"] = {
                    "multi_select": [{"name": tag} for tag in tags]
                }

            page_content = {
                "parent": {"database_id": self.database_id},
                "properties": properties,
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]
            }

            response = self.client.pages.create(**page_content)
            logger.info(f"Created new page in Notion: {title}")
            return response

        except Exception as e:
            logger.error(f"Error creating Notion page: {str(e)}")
            raise

    def update_page(self, page_id, title=None, content=None, tags=None):
        """Update an existing page in the Notion database"""
        try:
            properties = {}
            
            if title:
                properties["Name"] = {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }

            if tags:
                properties["Tags"] = {
                    "multi_select": [{"name": tag} for tag in tags]
                }

            if properties:
                self.client.pages.update(
                    page_id=page_id,
                    properties=properties
                )

            if content:
                # First, get existing blocks
                blocks = self.client.blocks.children.list(block_id=page_id)
                
                # Delete existing blocks
                for block in blocks["results"]:
                    self.client.blocks.delete(block_id=block["id"])

                # Add new content
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=[
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": content
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                )

            logger.info(f"Updated Notion page: {page_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating Notion page: {str(e)}")
            raise 