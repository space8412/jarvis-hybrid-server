import re
import dateparser

def extract_title(text):
    match = re.search(r'(회의|미팅|상담|방문|시공|공사)', text)
    return match.group(1) if match else None

def extract_date(text):
    dt = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'Asia/Seoul', 'TO_TIMEZONE': 'Asia/Seoul'})
    return dt.isoformat() if dt else None

def extract_category(text):
    for c in ['회의', '미팅', '상담', '방문', '시공', '공사']:
        if c in text:
            return c
    return None
