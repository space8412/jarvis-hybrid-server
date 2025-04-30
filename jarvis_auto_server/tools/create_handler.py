from flask import jsonify
from tools.parser import extract_title, extract_date, extract_category
from tools.gpt_agent import request_gpt_agent
from tools.session_manager import redis_client, SESSION_EXPIRY
import json, datetime, os
import requests

N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')

def handle_create(text, user_id, session_id):
    title = extract_title(text)
    date = extract_date(text)
    category = extract_category(text)

    missing = [f for f, v in {'title': title, 'date': date, 'category': category}.items() if not v]
    if len(missing) >= 2:
        ai_result = request_gpt_agent(text)
        title = title or ai_result.get('title')
        date = date or ai_result.get('date')
        category = category or ai_result.get('category')

    session_data = {
        'intent': 'create', 'user_id': user_id,
        'title': title, 'date': date, 'category': category,
        'created_at': datetime.datetime.now().isoformat()
    }
    redis_client.setex(f"jarvis:session:{session_id}", SESSION_EXPIRY, json.dumps(session_data))

    if not title or not date or not category:
        missing = [f for f in ['title', 'date', 'category'] if not session_data.get(f)]
        return jsonify({ 'success': True, 'session_id': session_id,
                         'message': f"다음 정보가 필요합니다: {', '.join(missing)}",
                         'missing_fields': missing })

    try:
        res = requests.post(N8N_WEBHOOK_URL, json=session_data)
        res.raise_for_status()
        return jsonify({ 'success': True, 'message': '일정이 등록되었습니다.', 'n8n_response': res.json() })
    except Exception as e:
        return jsonify({ 'success': False, 'message': f'n8n 전송 오류: {str(e)}' })
