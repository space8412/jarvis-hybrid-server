from utils import get_logger

logger = get_logger(__name__)

class MessageClassifier:
    def __init__(self):
        self.intent_keywords = {
            'task': ['할일', '작업', 'task', 'todo', '해야할'],
            'schedule': ['일정', '약속', 'schedule', 'appointment', '미팅'],
            'reminder': ['알림', '리마인더', 'reminder', '알려줘'],
            'query': ['질문', '문의', 'query', 'what', 'how', 'when', 'where', 'why'],
            'other': []
        }

    def classify(self, message: str) -> dict:
        """Classify a message into an intent category"""
        try:
            message = message.lower()
            
            # Check for each intent category
            for intent, keywords in self.intent_keywords.items():
                if any(keyword in message for keyword in keywords):
                    logger.info(f"Classified message as {intent}")
                    return {
                        "intent": intent,
                        "confidence": 0.8  # Simple keyword matching confidence
                    }
            
            # If no intent is matched, classify as 'other'
            logger.info("Classified message as other")
            return {
                "intent": "other",
                "confidence": 0.5
            }
            
        except Exception as e:
            logger.error(f"Error classifying message: {str(e)}")
            raise

    def extract_entities(self, message: str) -> dict:
        """Extract entities from the message"""
        try:
            entities = {
                "dates": [],
                "times": [],
                "task_names": [],
                "locations": []
            }
            
            # Add your entity extraction logic here
            # This is a placeholder implementation
            
            logger.info(f"Extracted entities from message")
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            raise 