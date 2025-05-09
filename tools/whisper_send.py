import os
import requests
import tempfile

# ✅ 환경변수에서 Whisper API 키 불러오기
WHISPER_API_KEY = os.getenv("WHISPER_API_KEY")

def transcribe(file_obj) -> str:
    """
    FastAPI의 UploadFile 객체를 받아 Whisper API로 전송해 텍스트를 반환합니다.
    """
    if not WHISPER_API_KEY:
        raise Exception("Whisper API 키가 설정되지 않았습니다.")

    # ✅ 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(file_obj.file.read())
        tmp_path = tmp.name

    # ✅ Whisper API 호출
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

    # ✅ 응답 검증 및 예외 처리
    if response.status_code != 200:
        raise Exception(f"Whisper API 오류: {response.status_code}, {response.text}")

    # ✅ 텍스트 반환
    return response.json().get("text", "")
