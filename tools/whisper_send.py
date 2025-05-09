import requests
import os

def send_to_whisper(audio_path: str) -> str:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"File not found: {audio_path}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("환경변수 OPENAI_API_KEY가 설정되지 않았습니다.")

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
