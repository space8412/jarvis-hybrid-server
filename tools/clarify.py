def clarify_intent(parsed: dict) -> dict:
    """
    실전 환경에서 사용하는 intent 분기 처리 함수
    - title, date, category: 일정 등록 (register_schedule)
    - origin_title, origin_date 존재: 일정 수정 (update_schedule)
    - title, date만 있을 경우: 일정 삭제 (delete_schedule)
    - 그 외는 unknown 처리
    """

    title = parsed.get("title")
    date = parsed.get("date")
    category = parsed.get("category")
    origin_title = parsed.get("origin_title")
    origin_date = parsed.get("origin_date")

    # ✅ 등록 조건: title/date/category 모두 있는 경우
    if title and date and category:
        parsed["intent"] = "register_schedule"

    # ✅ 수정 조건: 기존 일정의 title/date가 함께 존재할 때
    elif origin_title and origin_date:
        parsed["intent"] = "update_schedule"

    # ✅ 삭제 조건: origin은 없고 title/date만 있는 경우
    elif title and date:
        parsed["intent"] = "delete_schedule"

    # ❌ 조건 미달 시 unknown 처리
    else:
        parsed["intent"] = "unknown"

    return parsed
