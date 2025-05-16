import re
import logging
from typing import Dict, Optional
from datetime import datetime
import dateparser

from tools.gpt_utils import gpt_date_fallback  # ✅ GPT 보정 함수 불러오기

logger = logging.getLogger(__name__)

REGISTER_KEYWORDS = ["등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"]
DELETE_KEYWORDS = ["삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어", "제거해"]
UPDATE_KEYWORDS = ["수정", "변경", "바꿔", "미뤄", "조정", "업데이트", "늦게", "앞당겨", "취소하고", "대신", "반영해"]

CATEGORY_KEYWORDS = ["회의", "미팅", "약속", "상담", "콘텐츠", "개인", "시공", "공사"]

DATE_PATTERNS = [
    r"\d{1,2}월\s*\d{1,2}일\s*(오전|오후)?\s*\d{1,2}시",
    r"\d{1,2}월\s*\d{1,2}일",
    r"오늘", r"내일", r"모레", r"다음주\s*[월화수목금토일]요일"
]

def clarify_command(message: str) -> Dict[str, Optional[str]]:
    result = {
        "title": "",
        "start_date": "",
        "category": "",
        "intent": "",
        "origin_title": "",
        "origin_date": ""
    }

    try:
        for word in REGISTER_KEYWORDS:
            if word in message:
                result["intent"] = "register_schedule"
                break
        for word in DELETE_KEYWORDS:
            if word in message:
                result["intent"] = "delete_schedule"
                break
        for word in UPDATE_KEYWORDS:
            if word in message:
                result["intent"] = "update_schedule"
                break

        for keyword in CATEGORY_KEYWORDS:
            if keyword in message:
                result["category"] = keyword
                break

        # 날짜 추출
        date_regex = "|".join(DATE_PATTERNS)
        full_date_match = re.search(date_regex, message)

        parsed_date = None
        if full_date_match:
            date_str = full_date_match.group(0).strip()

            # ✅ 1차: dateparser
            parsed_date = dateparser.parse(
                date_str,
                languages=["ko"],
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": datetime.now(),
                    "TIMEZONE": "Asia/Seoul",
                    "RETURN_AS_TIMEZONE_AWARE": False,
                    "NORMALIZE": True
                }
            )

            # ✅ 2차: GPT 보정
            if not parsed_date:
                logger.warning(f"[clarify] dateparser 실패 → GPT 보정 시도: {date_str}")
                try:
                    gpt_result = gpt_date_fallback(date_str)
                    parsed_date = datetime.fromisoformat(gpt_result)
                    logger.info(f"[clarify] GPT 보정 성공 → {parsed_date.isoformat()}")
                except Exception:
                    logger.warning(f"[clarify] GPT 보정 실패")

        if parsed_date:
            result["start_date"] = parsed_date.isoformat()
        else:
            logger.warning(f"[clarify] 최종 날짜 파싱 실패: {message}")

        # 제목 추출
        if full_date_match:
            end = full_date_match.end()
            remaining = message[end:].strip()
            title_candidate = remaining

            for cmd in ["등록해줘", "추가해줘", "기록해줘", "예정"]:
                title_candidate = title_candidate.replace(cmd, "")

            if title_candidate.startswith("에 "):
                title_candidate = title_candidate[2:]

            result["title"] = title_candidate.strip()

        # ✅ 수정 명령이면 원래 제목/날짜를 복사
        if result["intent"] == "update_schedule":
            result["origin_title"] = result["title"]
            result["origin_date"] = result["start_date"]

        logger.debug(f"[clarify] 파싱 결과: {result}")
        return result

    except Exception as e:
        logger.error(f"[clarify] 파싱 오류: {str(e)}")
        return result
