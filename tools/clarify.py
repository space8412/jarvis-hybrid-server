def clarify_command(message: str) -> Tuple[str, str, str, str]:
    title = ""
    start_date = ""
    category = ""
    intent = ""

    try:
        # intent 및 title/date/category 추출
        date_patterns = [
            r"\d{1,2}월\s*\d{1,2}일",
            r"오늘",
            r"내일",
            r"모레",
            r"다음주\s*[월화수목금토일]요일"
        ]
        date_pattern = "|".join(date_patterns)

        if "등록" in message or "추가" in message:
            intent = "register_schedule"
            title_match = re.search(f"(.+?)({date_pattern})", message)
            if title_match:
                title = title_match.group(1).strip()

            date_match = re.search(date_pattern, message)
            if date_match:
                start_date = date_match.group(0)

        elif "삭제" in message or "제거" in message:
            intent = "delete_schedule"
            date_match = re.search(r"(\d{1,2}월\s*\d{1,2}일)", message)
            if date_match:
                start_date = date_match.group(1)

        category_keywords = ["회의", "미팅", "약속", "휴가", "이벤트"]
        for keyword in category_keywords:
            if keyword in message:
                category = keyword
                break

    except Exception as e:
        logger.error(f"명령 파싱 오류 발생: {str(e)}")

    return title, start_date, category, intent
