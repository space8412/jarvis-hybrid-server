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

# 환경변수 불러오기
REDIS_URL = os.environ.get('REDIS_URL')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
GPT_AGENT_URL = os.environ.get('GPT_AGENT_URL')

# Redis 연결
redis_client = redis.from_url(REDIS_URL)

# 세션 만료 시간
SESSION_EXPIRY = 3600

# 인텐트 키워드
INTENTS = {
    'create': ['등록', '추가', '만들어', '잡아', '넣어', '생성'],
    'update': ['수정', '변경', '바꿔', '업데이트'],
    'delete': ['삭제', '지워', '취소'],
    'read': ['조회', '확인', '보여줘', '알려줘']
}

# 주요 필드 추출 함수
def extract_title(text):
    match = re.search(r'(회의|미팅|상담|방문|시공|공사)', text)
    return match.group(1) if match else None

def extract_date(text):
    dt = dateparser.parse(text, settings={
        'PREFER_DATES_FROM': 'future',
        'TIMEZONE': 'Asia/Seoul',
        'TO_TIMEZONE': 'Asia/Seoul'
    })
    if dt:
        return dt.isoformat()

    # GPT Agent 호출 (timeout 10초 적용)
    try:
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}
        res = requests.post(GPT_AGENT_URL, json={'text': text}, headers=headers, timeout=10)
        if res.status_code == 200:
            ai_result = res.json()
            return ai_result.get('date')
    except Exception as e:
        print(f"[extract_date] GPT 호출 실패: {e}")
    return None

def extract_category(text):
    for keyword in ['회의', '미팅', '상담', '방문', '시공', '공사']:
        if keyword in text:
            return keyword
    return None

# GPT Agent 수동 호출
def request_gpt_agent(text):
    try:
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}
        res = requests.post(GPT_AGENT_URL, json={'text': text}, headers=headers, timeout=10)
        return res.json()
    except Exception as e:
        print(f"[GPT Agent] 호출 실패: {e}")
        return {}

# 인텐트 판별
def identify_intent(text):
    for intent, keywords in INTENTS.items():
        if any(k in text for k in keywords):
            return intent
    return 'create'

# 트리거 진입점
@app.route('/trigger', methods=['POST'])
def trigger():
    try:
        data = request.json
        user_input = data.get('text', '')
        user_id = data.get('user_id', 'default')
        session_id = str(uuid.uuid4())
        intent = identify_intent(user_input)

        if intent == 'create':
            return handle_create_intent(user_input, user_id, session_id)
        return jsonify({'success': False, 'message': f'[{intent}] 인텐트는 아직 구현되지 않았습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'오류 발생: {str(e)}'})

# 일정 등록 핸들러
def handle_create_intent(text, user_id, session_id):
    title = extract_title(text)
    date = extract_date(text)
    category = extract_category(text)

    if not all([title, date, category]):
        gpt_data = request_gpt_agent(text)
        title = title or gpt_data.get('title')
        date = date or gpt_data.get('date')
        category = category or gpt_data.get('category')

    session_data = {
        'intent': 'create',
        'user_id': user_id,
        'title': title,
        'date': date,
        'category': category,
        'created_at': datetime.now().isoformat()
    }

    redis_client.setex(f"jarvis:session:{session_id}", SESSION_EXPIRY, json.dumps(session_data))

    if not all([title, date, category]):
        missing = [k for k in ['title', 'date', 'category'] if not session_data.get(k)]
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f"다음 정보가 필요합니다: {', '.join(missing)}",
            'missing_fields': missing
        })

    try:
        res = requests.post(N8N_WEBHOOK_URL, json=session_data)
        return jsonify({'success': True, 'message': '등록 완료', 'n8n_response': res.json()})
    except Exception as e:
        return jsonify({'success': False, 'message': f'n8n 전송 실패: {str(e)}'})

# Agent 직접 호출용
@app.route('/agent', methods=['POST'])
def agent():
    try:
        user_input = request.json.get('text', '')
        return jsonify({
            'title': extract_title(user_input) or "상담",
            'date': extract_date(user_input),
            'category': extract_category(user_input) or "기타"
        })
    except Exception as e:
        return jsonify({'error': str(e)})

# WSGI
app = app
