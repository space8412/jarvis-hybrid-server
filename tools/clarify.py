import re
import os
import logging
from typing import Dict, Optional
from datetime import datetime
import dateparser
import openai  # ✅ GPT 호출용

logger = logging.getLogger(__name__)

# ✅ GPT API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

REGISTER_KEYWORDS = ["등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"]
DELETE_KEYWORDS = ["삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어", "제거해"]
UPDATE_KEYWORDS = ["수정", "변경", "바꿔", "미뤄", "조정", "업데이트", "늦게", "앞당겨", "취소하고", "대신", "반영해"]

CATEGORY_KEYWORDS = ["회의", "미팅", "약속", "상담", "콘텐츠", "개인", "시공", "공사"]

DATE_PATTERNS = [
    r"\d{1,2}월\s*\d{1,2}일\s*(오전|오후)?\s*\d{1,2}시",
    r"\d{1,2}월\s*\d{1,2}일",
    r"오늘", r"내일", r"모레", r"다음주\s*[월화수목금토일]요일"
]

# ✅ GPT로 날짜 보정 함수
def gpt_date_fallback(text: str) -> Optional[str]:
    try:
        prompt = f"'{text}' 를 ISO 8601 형식의 날짜-시간(예: 2025-05-18T14:00:00)으로 변환해줘. 결과만 딱 써줘."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        iso_str = response.choices[0].message.content.strip()
        # ✅ 형식 검증
        datetime.fromisoformat(iso_str)
        return iso_str
    except Exception as e:
        logger.error(f"[GPT 보정 실패] {str(e)}")
        return None

# ✅ 명령 해석 함수
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

            # ✅ 1차: dateparser 시도
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

            # ✅ 2차: GPT 보정 시도
            if not parsed_date:
                logger.warning(f"[clarify] dateparser 실패 → GPT 보정 시도: {date_str}")
                gpt_result = gpt_date_fallback(date_str)
                if gpt_result:
                    parsed_date = datetime.fromisoformat(gpt_result)
                    logger.info(f"[clarify] GPT 보정 성공 → {parsed_date.isoformat()}")

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

        logger.debug(f"[clarify] 파싱 결과: {result}")
        return result

    except Exception as e:
        logger.error(f"[clarify] 파싱 오류: {str(e)}")
        return result
