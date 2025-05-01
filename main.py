from flask import Flask, request, jsonify
import os
import dateparser
import re

app = Flask(__name__)

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

def extract_title(text):
    match = re.search(r'(회의|미팅|상담|방문|시공|공사)', text)
    return match.group(1) if match else None

def extract_date(text):
    dt = dateparser.parse(text, settings={
        'PREFER_DATES_FROM': 'future',
        'TIMEZONE': 'Asia/Seoul',
        'TO_TIMEZONE': 'Asia/Seoul'
    })
    return dt.isoformat() if dt else None

def extract_category(text):
    categories = ['회의', '미팅', '상담', '방문', '시공', '공사']
    for cat in categories:
        if cat in text:
            return cat
    return None

if __name__ == '__main__':
    app.run(debug=True)

app = app