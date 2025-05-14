import os
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

def verify_database():
    """
    연결된 Notion 데이터베이스의 속성을 검증합니다.
    """  
    try:
        database_id = os.environ["NOTION_DATABASE_ID"]
        database = notion.databases.retrieve(database_id=database_id)
        properties = database["properties"]

        assert "Name" in properties, "'Name' 속성이 없습니다."
        assert properties["Name"]["type"] == "title", "'Name'은 title 타입이어야 합니다."
        
        assert "Date" in properties, "'Date' 속성이 없습니다."
        assert properties["Date"]["type"] == "date", "'Date'는 date 타입이어야 합니다."
        
        assert "Category" in properties, "'Category' 속성이 없습니다."  
        assert properties["Category"]["type"] == "select", "'Category'는 select 타입이어야 합니다."
        
        print("데이터베이스 검증 완료. 모든 속성이 올바르게 설정되었습니다.")
    except AssertionError as e:
        print(f"데이터베이스 검증 실패: {str(e)}")  
    except Exception as e:
        print(f"데이터베이스 검증 중 오류 발생: {e}")
        
if __name__ == "__main__":
    verify_database()