import os
import logging
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger(__name__)

# ✅ 최신 openai SDK 방식 (v1.x 이상)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def gpt_date_fallback(text: str) -> str:
    """
    자연어 날짜 문자열을 GPT로 ISO 8601 포맷으로 변환
    예) "5월 18일 오후 2시" → "2025-05-18T14:00:00"
    """
    try:
        prompt = f"'{text}' 를 ISO 8601 형식(예: 2025-05-18T14:00:00)으로 변환해줘. 결과만 딱 한 줄로 줘."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        iso_text = response.choices[0].message.content.strip()
        datetime.fromisoformat(iso_text)  # ISO 형식 검증
        return iso_text

    except Exception as e:
        logger.error(f"[gpt_date_fallback] GPT 보정 실패: {str(e)}")
        raise ValueError("GPT를 통한 날짜 보정 실패")
