from datetime import datetime

def normalize_notion_date(iso_string: str) -> dict:
    """
    Notion에 전달할 수 있도록 날짜 값을 정제합니다.
    - 시간 정보가 있으면 'date_time' 키로 반환 (타임존 제거)
    - 종일 일정은 'date' 키로 반환
    """
    try:
        if "T" in iso_string:
            dt = datetime.fromisoformat(iso_string)
            return {"date_time": dt.strftime("%Y-%m-%dT%H:%M:%S")}
        else:
            return {"date": iso_string}
    except Exception:
        return {"date": iso_string}
