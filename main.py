from flask import Flask, request, jsonify
import dateparser
import re

app = Flask(__name__)

def extract_title(text):
    match = re.search(r'(회의|미팅|상담|방문|시공|공사)', text)
    return match.group(1) if match else "상담"

def extract_date(text):
    dt = dateparser.parse(text, settings={
        'PREFER_DATES_FROM': 'future',
        'TIMEZONE': 'Asia/Seoul',
        'TO_TIMEZONE': 'Asia/Seoul',
        'RETURN_AS_TIMEZONE_AWARE': False
    })
    return dt.isoformat() if dt else None

def extract_category(text):
    for word in ['회의', '미팅', '상담', '방문', '시공', '공사']:
        if word in text:
            return word
    return "기타"

@app.route('/agent', methods=['POST'])
def agent():
    try:
        data = request.get_json()
        text = data.get('text', '')
        return jsonify({
            "title": extract_title(text),
            "date": extract_date(text),
            "category": extract_category(text)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
