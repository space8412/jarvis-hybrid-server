import os
import json
import logging
from openai import OpenAI
from utils import validate_env_variables, APIError, ValidationError

logger = logging.getLogger(__name__)

# 환경 변수 검증
validate_env_variables({
    "OPENAI_API_KEY": "OpenAI API key is required"
})

# ✅ GPT API 키 불러오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def parse_command(text: str) -> dict:
    """
    GPT를 호출하여 자연어 명령어를 intent, title, date, category 등으로 분석
    """
    if not isinstance(text, str) or not text.strip():
        raise ValidationError("text must be a non-empty string")

    prompt = f"""
    다음 명령어를 분석해서 JSON으로 반환해줘. 조건은 다음과 같아:
    - intent: register_schedule, delete_schedule, update_schedule 중 하나
    - title: 장소나 키워드를 제목으로 사용
    - date: ISO 8601 형식으로 (예: 2024-05-15T15:00:00)
    - category: 회의, 상담, 시공, 공사, 미정 등 중 하나
    명령어: {text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "너는 일정 자동화를 위한 분석 비서야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        
        # 응답 형식 검증
        required_fields = ["intent", "title", "date", "category"]
        if not all(field in result for field in required_fields):
            raise ValidationError("GPT response missing required fields")

        logger.info(f"Successfully parsed command: {result}")
        return result

    except json.JSONDecodeError:
        logger.error("GPT response is not valid JSON")
        raise ValidationError("GPT 응답이 JSON 형식이 아닙니다.")
    except Exception as e:
        logger.error(f"Error in parse_command: {str(e)}")
        raise APIError(f"Error parsing command: {str(e)}")
