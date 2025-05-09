import requests
import os

def send_to_whisper(audio_path: str) -> str:
    api_key = os.getenv("WHISPER_API_KEY")  # 🔹 환경변수에서 키 불러오기
    if not api_key:
        raise Exception("WHISPER_API_KEY 환경변수가 설정되어 있지 않습니다.")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"File not found: {audio_path}")

    with open(audio_path, "rb") as audio_file:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            files={
                "file": (os.path.basename(audio_path), audio_file, "audio/wav")
            },
            data={
                "model": "whisper-1"
            }
        )

    if response.status_code != 200:
        raise Exception(f"Whisper API error: {response.status_code}, {response.text}")

    return response.json().get("text", "")
