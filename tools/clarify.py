import re
import logging
from typing import Dict, Optional
import dateparser

logger = logging.getLogger(__name__)

REGISTER_KEYWORDS = ["등록", "추가", "넣어", "잡아", "기록해", "예정", "메모", "잊지 말고", "남겨", "저장"]
DELETE_KEYWORDS = ["삭제", "지워", "취소", "없애", "제거", "빼", "날려", "말소", "무시", "필요 없어", "제거해"]
UPDATE_KEYWORDS = ["수정", "변경", "바꿔", "미뤄", "조정", "업데이트", "늦게", "앞당겨", "취소하고", "대신", "반영해"]
CATEGORY_KEYWORDS = ["회의", "미팅", "상담", "시공", "공사", "개인", "콘텐츠"]

def extract_date(text: str) -> Optional[str]:
    date = dateparser.parse(text, languages=["ko"], settings={"PREFER_DATES_FROM": "future"})
    if date:
        return date.isoformat()
    return None

def extract_intent(text: str) -> Optional[str]:
    for word in DELETE_KEYWORDS:
        if word in text:
            return "delete_schedule"
    for word in UPDATE_KEYWORDS:
        if word in text:
            return "update_schedule"
    for word in REGISTER_KEYWORDS:
        if word in text:
            return "register_schedule"
    return None

def extract_category(text: str) -> str:
    for keyword in CATEGORY_KEYWORDS:
        if keyword in text:
            return keyword
    return "기타"

def extract_title(text: str) -> str:
    """
    메시지에서 날짜, 명령어 제거 후 핵심 일정 제목만 추출
    """
    # 날짜/시간 제거 (예: "5월 18일 오후 2시")
    text = re.sub(r"\d{1,2}[월.]\s*\d{1,2}[일.]?\s*(오전|오후)?\s*\d{1,2}시", "", text)

    # 명령어 제거
    for cmd in REGISTER_KEYWORDS + DELETE_KEYWORDS + UPDATE_KEYWORDS + ["해줘", "해", "줘"]:
        text = text.replace(cmd, "")

    # 조사 제거
    for suffix in ["에", "는", "을", "를", "도", "한테", "까지", "하고"]:
        text = text.replace(suffix, "")

    return text.strip()

def clarify_command(text: str) -> Dict[str, str]:
    try:
        intent = extract_intent(text)
        raw_date = extract_date(text)
        title = extract_title(text)
        category = extract_category(text)

        parsed = {
            "intent": intent or "",
            "title": title,
            "start_date": raw_date or "",
            "category": category,
            "origin_title": "",
            "origin_date": "",
        }

        if not raw_date:
            logger.warning("[clarify] dateparser 실패 → GPT 보정 시도: %s", text)
            try:
                from openai import OpenAI
                import os
                client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
                prompt = (
                    f"'5월 18일 오후 2시'은 2025년을 기준으로 한 한국 시간의 날짜와 시간입니다.\n"
                    f"이를 ISO 8601 형식(예: 2025-05-18T14:00:00)으로 변환해줘.\n"
                    f"결과는 날짜와 시간만 포함된 한 줄짜리 ISO 형식 문자열로만 줘.\n"
                    f"불확실하더라도 예측해서 완성해줘.\n"
                )
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                iso_date = response.choices[0].message.content.strip()
                parsed["start_date"] = iso_date
                logger.info("[clarify] GPT 보정 성공 → %s", iso_date)
            except Exception as e:
                logger.error("[clarify] GPT 보정 실패: %s", str(e))

        logger.debug("[clarify] 파싱 결과: %s", parsed)
        return parsed

    except Exception as e:
        logger.error(f"[clarify] 예외 발생: {str(e)}")
        return {
            "intent": "",
            "title": "",
            "start_date": "",
            "category": "",
            "origin_title": "",
            "origin_date": "",
        }
