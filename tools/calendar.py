import logging
from datetime import datetime
from dateutil import tz
from dateutil.parser import isoparse
from utils import ValidationError, config

logger = logging.getLogger(__name__)

def correct_datetime_format(text: str, result: dict) -> dict:
    """시간 정보가 누락되었거나 잘못된 경우 보정해주는 함수"""
    try:
        if not isinstance(result, dict):
            raise ValidationError("result must be a dictionary")

        if "T00:00:00" in result.get("date", ""):
            if "오전" not in text:
                result["date"] = result["date"].replace("T00:00:00", "T15:00:00")

        if result.get("date"):
            dt = isoparse(result["date"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz.gettz(config.timezone))
            result["date"] = dt.isoformat()

    except Exception as e:
        logger.error(f"Error in datetime format correction: {str(e)}")
        raise

    return result
