from flask import Flask, request, jsonify
import redis
import json
import os
import dateparser
import uuid
import requests
from datetime import datetime
import re

app = Flask(__name__)

# Redis 연결
REDIS_URL = os.environ.get('REDIS_URL')
redis_client = redis.from_url(REDIS_URL)

# 외부 API 환경변수
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
GPT_AGENT_URL = os.environ.get('GPT_AGENT_URL')

SESSION_EXPIRY = 3600

# 인텐트 키워드 정의
INTENTS = {
    'create': ['등록', '추가', '만들어', '잡아', '넣어', '생성'],
    'update': ['수정', '변경', '바꿔', '업데이트', '수정해'],
    'delete': ['취소', '삭제', '지워', '없애', '취소해'],
    'read': ['조회', '보여줘', '알려줘', '확인', '뭐가 있어', '일정 확인']
}

# 유틸리티 함수
def extract_title(text):
    match = re.search(r'(\d+월\s*\d+일)?\s*(오전|오후)?\s*\d{1,2}시.*?\s*(회의|미팅|상담|방문|시공|공사)', text)
    return match.group(3) if match else None

def extract_date(text):
    dt = dateparser.parse(text, settings={
        'PREFER_DATES_FROM': 'future',
        'TIMEZONE': 'Asia/Seoul',
        'TO_TIMEZONE': 'Asia/Seoul'
    })
    if dt:
        return dt.isoformat()
    try:
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}
        res = requests.post(GPT_AGENT_URL, json={'text': text}, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json().get('date')
    except Exception as e:
        print(f"extract_date 오류: {e}")
    return None

def extract_category(text):
    for cat in ['회의', '미팅', '상담', '방문', '시공', '공사']:
        if cat in text:
            return cat
    return None

def identify_intent(text):
    text = text.lower()
    for intent, keywords in INTENTS.items():
        if any(k in text for k in keywords):
            return intent
    return 'create'

# n8n 전송 함수
def send_to_n8n(data, intent):
    try:
        res = requests.post(N8N_WEBHOOK_URL, json=data, timeout=10)
        res.raise_for_status()
        return jsonify({'success': True, 'message': '자동화가 실행되었습니다.', 'n8n_response': res.json()})
    except Exception as e:
        print(f"send_to_n8n 오류: {e}")
        return jsonify({'success': False, 'message': f'n8n 전송 실패: {str(e)}'})

# /trigger 엔드포인트
@app.route('/trigger', methods=['POST'])
def trigger():
    try:
        data = request.json
        user_input = data.get('text', '')
        user_id = data.get('user_id', 'default_user')
        intent = identify_intent(user_input)
        session_id = str(uuid.uuid4())

        if intent == 'create':
            return handle_create_intent(user_input, user_id, session_id)
        else:
            return jsonify({'success': False, 'message': '현재는 create만 지원합니다.'})
    except Exception as e:
        print(f"/trigger 오류: {e}")
        return jsonify({'success': False, 'message': f'오류: {str(e)}'})

# create intent 처리
def handle_create_intent(text, user_id, session_id):
    title = extract_title(text)
    date = extract_date(text)
    category = extract_category(text)

    # 값 누락 시 GPT Agent 호출
    missing = [k for k, v in {'title': title, 'date': date, 'category': category}.items() if not v]
    if len(missing) >= 2:
        try:
            headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}
            res = requests.post(GPT_AGENT_URL, json={'text': text}, headers=headers, timeout=10)
            if res.status_code == 200:
                ai_result = res.json()
                title = title or ai_result.get('title')
                date = date or ai_result.get('date')
                category = category or ai_result.get('category')
        except Exception as e:
            print(f"GPT Agent 호출 오류: {e}")

    session_data = {
        'intent': 'create',
        'user_id': user_id,
        'title': title,
        'date': date,
        'category': category,
        'created_at': datetime.now().isoformat()
    }

    redis_client.setex(f"jarvis:session:{session_id}", SESSION_EXPIRY, json.dumps(session_data))

    missing = [f for f in ['title', 'date', 'category'] if not session_data.get(f)]
    if missing:
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f"다음 정보가 필요합니다: {', '.join(missing)}",
            'missing_fields': missing
        })

    return send_to_n8n(session_data, 'create')

# /agent 엔드포인트
@app.route('/agent', methods=['POST'])
def agent():
    try:
        user_input = request.json.get('text', '')
        title = extract_title(user_input) or "상담"
        date = extract_date(user_input)
        category = extract_category(user_input) or "기타"
        return jsonify({
            'title': title,
            'date': date,
            'category': category
        })
    except Exception as e:
        return jsonify({'error': str(e)})

# 로컬 실행
if __name__ == '__main__':
    app.run(debug=True)

# WSGI 서버용
app = app
