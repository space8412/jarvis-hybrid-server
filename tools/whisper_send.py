# tools/whisper_send.py

import os
import requests
import tempfile

WHISPER_API_KEY = os.getenv("WHISPER_API_KEY")

def transcribe(file_obj) -> str:
    if not WHISPER_API_KEY:
        raise Exception("Whisper API 키가 설정되지 않았습니다.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(file_obj.file.read())
        tmp_path = tmp.name

    with open(tmp_path, "rb") as audio_file:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={
                "Authorization": f"Bearer {WHISPER_API_KEY}"
            },
            files={
                "file": (os.path.basename(tmp_path), audio_file, "audio/wav")
            },
            data={
                "model": "whisper-1"
            }
        )

    if response.status_code != 200:
        raise Exception(f"Whisper API 오류: {response.status_code}, {response.text}")

    return response.json().get("text", "")
