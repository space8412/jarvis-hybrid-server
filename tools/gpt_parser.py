from openai import OpenAI
from config import OPENAI_API_KEY
from utils import get_logger

logger = get_logger(__name__)

class GPTParser:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview"

    def parse_message(self, message: str, context: str = None) -> str:
        """Parse a message using GPT and return the response"""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant that helps users manage their tasks and schedule."}
            ]
            
            if context:
                messages.append({"role": "system", "content": f"Context: {context}"})
            
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            parsed_response = response.choices[0].message.content
            logger.info(f"Successfully parsed message with GPT")
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error parsing message with GPT: {str(e)}")
            raise

    def classify_intent(self, message: str) -> dict:
        """Classify the intent of a message using GPT"""
        try:
            messages = [
                {"role": "system", "content": "You are an intent classifier. Classify the user's message into one of these categories: task, schedule, reminder, query, or other. Also extract any relevant entities like dates, times, or task names."},
                {"role": "user", "content": message}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=150
            )
            
            classification = response.choices[0].message.content
            logger.info(f"Successfully classified message intent")
            return {"classification": classification}
            
        except Exception as e:
            logger.error(f"Error classifying message intent: {str(e)}")
            raise 