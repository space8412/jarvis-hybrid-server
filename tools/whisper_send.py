import os
import requests

def send_to_whisper(audio_path: str) -> str:
    api_key = os.getenv("WHISPER_API_KEY")  # ✅ Whisper 전용 키

    if not api_key:
        raise EnvironmentError("WHISPER_API_KEY not found in environment variables")

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
