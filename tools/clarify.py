from utils import get_logger
from .gpt_parser import GPTParser
from .parser import Parser

logger = get_logger(__name__)

class MessageClarifier:
    def __init__(self):
        self.gpt = GPTParser()
        self.parser = Parser()

    def clarify_message(self, message: str) -> dict:
        """Clarify the user's message and extract structured information"""
        try:
            # Get GPT's understanding of the message
            clarification_prompt = f"""
            다음 메시지를 분석하고 다음 정보를 추출해주세요:
            1. 의도 (task, schedule, reminder, query 중 하나)
            2. 주요 행동/작업
            3. 날짜/시간 정보
            4. 우선순위 (높음, 중간, 낮음)
            5. 추가 컨텍스트나 세부사항

            메시지: {message}

            JSON 형식으로 응답해주세요.
            """

            gpt_response = self.gpt.parse_message(clarification_prompt)
            
            # Parse date and time information
            start_time, end_time = self.parser.parse_datetime(message)
            task_name = self.parser.extract_task_name(message)

            # Combine GPT's understanding with parsed information
            clarification = {
                "original_message": message,
                "task_name": task_name,
                "start_time": start_time,
                "end_time": end_time,
                "gpt_analysis": gpt_response
            }

            logger.info(f"Clarified message: {message}")
            return clarification

        except Exception as e:
            logger.error(f"Error clarifying message: {str(e)}")
            return {
                "original_message": message,
                "error": str(e)
            }

    def get_clarification_questions(self, message: str) -> list:
        """Generate questions to clarify ambiguous messages"""
        try:
            prompt = f"""
            다음 메시지에서 불명확한 부분이 있다면, 사용자에게 물어볼 질문들을 생성해주세요.
            각 질문은 메시지를 더 명확하게 이해하는데 도움이 되어야 합니다.

            메시지: {message}

            JSON 형식으로 응답해주세요.
            """

            gpt_response = self.gpt.parse_message(prompt)
            logger.info(f"Generated clarification questions for message: {message}")
            return gpt_response

        except Exception as e:
            logger.error(f"Error generating clarification questions: {str(e)}")
            return []

    def format_clarified_message(self, clarification: dict) -> str:
        """Format the clarified message into a human-readable string"""
        try:
            formatted = f"""
            메시지 분석 결과:
            - 원본 메시지: {clarification['original_message']}
            - 작업명: {clarification['task_name']}
            """

            if clarification.get('start_time'):
                formatted += f"- 시작 시간: {clarification['start_time'].strftime('%Y-%m-%d %H:%M')}\n"
            if clarification.get('end_time'):
                formatted += f"- 종료 시간: {clarification['end_time'].strftime('%Y-%m-%d %H:%M')}\n"

            if clarification.get('gpt_analysis'):
                formatted += f"\nGPT 분석:\n{clarification['gpt_analysis']}"

            return formatted

        except Exception as e:
            logger.error(f"Error formatting clarified message: {str(e)}")
            return str(clarification) 