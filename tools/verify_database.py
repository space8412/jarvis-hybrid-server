from notion_client import Client
from config import NOTION_API_KEY, NOTION_DATABASE_ID
from utils import get_logger

logger = get_logger(__name__)

class DatabaseVerifier:
    def __init__(self):
        self.client = Client(auth=NOTION_API_KEY)
        self.database_id = NOTION_DATABASE_ID
        self.required_properties = {
            "Name": "title",
            "Tags": "multi_select",
            "Status": "select",
            "Priority": "select",
            "Due Date": "date"
        }

    def verify_database(self) -> bool:
        """Verify that the Notion database has all required properties"""
        try:
            # Get database structure
            database = self.client.databases.retrieve(database_id=self.database_id)
            properties = database.get("properties", {})

            # Check for required properties
            missing_properties = []
            for prop_name, prop_type in self.required_properties.items():
                if prop_name not in properties:
                    missing_properties.append(prop_name)
                elif properties[prop_name]["type"] != prop_type:
                    logger.warning(f"Property '{prop_name}' has wrong type. Expected: {prop_type}, Got: {properties[prop_name]['type']}")

            if missing_properties:
                logger.error(f"Missing required properties: {', '.join(missing_properties)}")
                return False

            logger.info("Database verification successful")
            return True

        except Exception as e:
            logger.error(f"Error verifying database: {str(e)}")
            return False

    def create_missing_properties(self) -> bool:
        """Create missing properties in the Notion database"""
        try:
            # Get current database structure
            database = self.client.databases.retrieve(database_id=self.database_id)
            properties = database.get("properties", {})

            # Prepare properties to add
            properties_to_add = {}
            for prop_name, prop_type in self.required_properties.items():
                if prop_name not in properties:
                    if prop_type == "title":
                        properties_to_add[prop_name] = {
                            "title": {}
                        }
                    elif prop_type == "multi_select":
                        properties_to_add[prop_name] = {
                            "multi_select": {
                                "options": []
                            }
                        }
                    elif prop_type == "select":
                        properties_to_add[prop_name] = {
                            "select": {
                                "options": []
                            }
                        }
                    elif prop_type == "date":
                        properties_to_add[prop_name] = {
                            "date": {}
                        }

            if properties_to_add:
                # Update database with new properties
                self.client.databases.update(
                    database_id=self.database_id,
                    properties=properties_to_add
                )
                logger.info(f"Added missing properties: {', '.join(properties_to_add.keys())}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error creating missing properties: {str(e)}")
            return False

    def verify_and_fix_database(self) -> bool:
        """Verify database structure and create missing properties if needed"""
        try:
            if not self.verify_database():
                logger.info("Attempting to create missing properties...")
                return self.create_missing_properties()
            return True

        except Exception as e:
            logger.error(f"Error in verify_and_fix_database: {str(e)}")
            return False 