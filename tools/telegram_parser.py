import os
import logging
import tempfile
from openai import OpenAI
from utils import validate_env_variables, APIError, ValidationError, async_api_call

logger = logging.getLogger(__name__)

# 환경 변수 검증
validate_env_variables({
    "OPENAI_API_KEY": "OpenAI API key is required",
    "TELEGRAM_TOKEN": "Telegram token is required"
})

# ✅ Whisper 사용을 위한 GPT API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI(api_key=OPENAI_API_KEY)

async def extract_text_from_telegram(data: dict) -> str:
    """
    텔레그램 메시지에서 텍스트 또는 음성 → 텍스트 추출
    """
    if not isinstance(data, dict):
        raise ValidationError("data must be a dictionary")

    message = data.get("message", {})
    tmp_path = None

    try:
        # 음성 메시지 처리
        if "voice" in message:
            file_id = message["voice"]["file_id"]
            file_info = await async_api_call(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile",
                {"Content-Type": "application/json"},
                params={"file_id": file_id}
            )
            
            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

            # 음성 파일 다운로드
            response = await async_api_call(file_url, {})
            
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
                tmp_file.write(response)
                tmp_path = tmp_file.name

            # Whisper로 변환
            with open(tmp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            return transcript.strip()

        # 텍스트 메시지 처리
        elif "text" in message:
            return message["text"]

        # 그 외 fallback
        return data.get("text", "")

    except Exception as e:
        logger.error(f"Error in extract_text_from_telegram: {str(e)}")
        raise APIError(f"Error extracting text: {str(e)}")

    finally:
        # 임시 파일 정리
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.error(f"Error deleting temporary file: {str(e)}")
