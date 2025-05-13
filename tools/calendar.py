from datetime import datetime
from dateutil import tz
from dateutil.parser import isoparse

def correct_datetime_format(text: str, result: dict) -> dict:
    """시간 정보가 누락되었거나 잘못된 경우 보정해주는 함수"""
    try:
        if "T00:00:00" in result.get("date", ""):
            if "오전" not in text:
                result["date"] = result["date"].replace("T00:00:00", "T15:00:00")

        if result.get("date"):
            dt = isoparse(result["date"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz.gettz("Asia/Seoul"))
            result["date"] = dt.isoformat()

    except Exception:
        pass

    return result
