from flask import Flask, request, jsonify
import os
import re
import dateparser
import requests

app = Flask(__name__)

# 환경변수
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 날짜 추출 함수
def extract_date(text):
    # 1차 시도: dateparser
    dt = dateparser.parse(text, settings={
        'PREFER_DATES_FROM': 'future',
        'TIMEZONE': 'Asia/Seoul',
        'TO_TIMEZONE': 'Asia/Seoul'
    })
    if dt:
        return dt.isoformat()

    # 2차 시도: GPT Agent 서버에 위임
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        res = requests.post(
            os.environ.get("GPT_AGENT_URL"),
            json={"text": text},
            headers=headers,
            timeout=10
        )
        if res.status_code == 200:
            return res.json().get("date")
    except Exception as e:
        print(f"GPT Agent 호출 실패: {e}")
    return None

# 카테고리 추출 함수
def extract_category(text):
    categories = ['회의', '미팅', '상담', '방문', '시공', '공사']
    for cat in categories:
        if cat in text:
            return cat
    return "기타"

# 타이틀 추출 함수
def extract_title(text):
    match = re.search(r'(회의|미팅|상담|방문|시공|공사)', text)
    return match.group(1) if match else "상담"

# ✅ 핵심: /agent 라우트
@app.route('/agent', methods=['POST'])
def agent():
    try:
        user_input = request.json.get("text", "")
        return jsonify({
            "title": extract_title(user_input),
            "date": extract_date(user_input),
            "category": extract_category(user_input)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# WSGI용 앱 노출
app = app
