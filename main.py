from flask import Flask, request, jsonify
import redis
import json
import os
import dateparser
import uuid
import requests
from datetime import datetime, timedelta
import re

app = Flask(__name__)

# Redis 연결
REDIS_URL = os.environ.get('REDIS_URL')
redis_client = redis.from_url(REDIS_URL)

# n8n Webhook URL
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')

# OpenAI API 설정 (조건부 호출용)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
GPT_AGENT_URL = os.environ.get('GPT_AGENT_URL')  # ex: https://your-agent-server.com/agent

# 세션 만료 시간
SESSION_EXPIRY = 3600

# 인텐트 정의
INTENTS = {
    'create': ['등록', '추가', '만들어', '잡아', '넣어', '생성'],
    'update': ['수정', '변경', '바꿔', '업데이트', '수정해'],
    'delete': ['취소', '삭제', '지워', '없애', '취소해'],
    'read': ['조회', '보여줘', '알려줘', '확인', '뭐가 있어', '일정 확인']
}

# ======================== 유틸리티 함수 ============================

def extract_title(text):
    match = re.search(r'(회의|미팅|상담|방문|시공|공사)', text)
    return match.group(1) if match else None

def extract_date(text):
    dt = dateparser.parse(text, settings={
        'PREFER_DATES_FROM': 'future',
        'TIMEZONE': 'Asia/Seoul',
        'TO_TIMEZONE': 'Asia/Seoul',
        'RETURN_AS_TIMEZONE_AWARE': False
    })
    # 날짜 유효성 검사 추가
    if dt and dt.year and dt.month and dt.day:
        return dt.isoformat()

    # 실패 시 GPT Agent 호출
    try:
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}
        res = requests.post(GPT_AGENT_URL, json={'text': text}, headers=headers)
        if res.status_code == 200:
            ai_result = res.json()
            return ai_result.get('date')
    except Exception as e:
        print(f"extract_date 오류: {e}")
        return None

def extract_category(text):
    categories = ['회의', '미팅', '상담', '방문', '시공', '공사']
    for cat in categories:
        if cat in text:
            return cat
    return None

# ======================== 외부 연동 함수 ============================

def send_to_n8n(data, intent):
    try:
        res = requests.post(N8N_WEBHOOK_URL, json=data)
        res.raise_for_status()
        return jsonify({ 'success': True, 'message': '자동화가 실행되었습니다.', 'n8n_response': res.json() })
    except Exception as e:
        print(f"send_to_n8n 오류: {e}")
        return jsonify({ 'success': False, 'message': f'n8n 전송 실패: {str(e)}' })

def request_gpt_agent(text):
    try:
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}
        res = requests.post(GPT_AGENT_URL, json={'text': text}, headers=headers)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"GPT Agent 호출 오류: {e}")
        return { 'error': str(e) }

# ======================== 트리거 엔드포인트 ============================

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
        elif intent == 'update':
            return handle_update_intent(user_input, user_id, session_id)
        elif intent == 'delete':
            return handle_delete_intent(user_input, user_id, session_id)
        elif intent == 'read':
            return handle_read_intent(user_input, user_id, session_id)
        else:
            return jsonify({'success': False, 'message': '지원하지 않는 인텐트입니다.'})
    except Exception as e:
        print(f"/trigger 처리 중 오류: {e}")
        return jsonify({'success': False, 'message': f'오류: {str(e)}'})

# ======================== 핸들러 구현 ============================

def handle_create_intent(text, user_id, session_id):
    title = extract_title(text)
    date = extract_date(text)
    category = extract_category(text)

    missing = [f for f, v in {'title': title, 'date': date, 'category': category}.items() if not v]
    if len(missing) >= 2:
        ai_result = request_gpt_agent(text)
        if 'title' in ai_result:
            title = ai_result['title']
        if 'date' in ai_result:
            date = ai_result['date']
        if 'category' in ai_result:
            category = ai_result['category']

    session_data = {
        'intent': 'create',
        'user_id': user_id,
        'title': title,
        'date': date,
        'category': category,
        'created_at': datetime.now().isoformat()
    }

    missing = [f for f in ['title', 'date', 'category'] if not session_data.get(f)]
    redis_client.setex(f"jarvis:session:{session_id}", SESSION_EXPIRY, json.dumps(session_data))

    if missing:
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f"다음 정보가 필요합니다: {', '.join(missing)}",
            'missing_fields': missing
        })

    return send_to_n8n(session_data, 'create')

# ======================== /agent 엔드포인트 ============================

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
        print(f"/agent 오류: {e}")
        return jsonify({'error': str(e)})

# ======================== 인텐트 판별 ============================

def identify_intent(text):
    text = text.lower()
    for intent, keywords in INTENTS.items():
        if any(k in text for k in keywords):
            return intent
    return 'create'

# ======================== 로컬 실행 ============================

if __name__ == '__main__':
    app.run(debug=True)

# WSGI용으로 Flask 인스턴스를 노출
app = app
