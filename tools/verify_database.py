import os
from notion_client import Client
import logging

logger = logging.getLogger(__name__)

notion = Client(auth=os.environ["NOTION_TOKEN"])

def verify_database():
    """
    연결된 Notion 데이터베이스의 속성을 검증합니다.
    """
    try:
        database_id = os.environ["NOTION_DATABASE_ID"]
        database = notion.databases.retrieve(database_id=database_id)
        properties = database["properties"]

        assert "일정 제목" in properties, "'일정 제목' 속성이 없습니다."
        assert properties["일정 제목"]["type"] == "title", "'일정 제목'은 title 타입이어야 합니다."
        
        assert "날짜" in properties, "'날짜' 속성이 없습니다."
        assert properties["날짜"]["type"] == "date", "'날짜'는 date 타입이어야 합니다."
        
        assert "유형" in properties, "'유형' 속성이 없습니다."  
        assert properties["유형"]["type"] == "select", "'유형'은 select 타입이어야 합니다."
        
        print("데이터베이스 검증 완료. 모든 속성이 올바르게 설정되었습니다.")
    except AssertionError as e:
        print(f"데이터베이스 검증 실패: {str(e)}")  
    except Exception as e:
        print(f"데이터베이스 검증 중 오류 발생: {e}")
        
def verify_environment() -> bool:
    """
    필수 환경변수의 존재 여부를 검증합니다.
    
    :return: 모든 필수 환경변수가 존재하면 True, 아니면 False
    """
    required_vars = [
        "NOTION_TOKEN",
        "NOTION_DATABASE_ID",
        "TELEGRAM_BOT_TOKEN",
        "OPENAI_API_KEY",
        "GOOGLE_CALENDAR_CREDENTIALS"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"누락된 필수 환경변수: {', '.join(missing_vars)}")
        return False
    
    return True

if __name__ == "__main__":
    verify_database()
