import os
import requests
import tempfile
from openai import OpenAI

# ✅ Whisper 사용을 위한 GPT API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI(api_key=OPENAI_API_KEY)

def extract_text_from_telegram(data: dict) -> str:
    """
    텔레그램 메시지에서 텍스트 또는 음성 → 텍스트 추출
    """
    message = data.get("message", {})

    # 음성 메시지 처리
    if "voice" in message:
        file_id = message["voice"]["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
        file_path = file_info["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

        response = requests.get(file_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name

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
