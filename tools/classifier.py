def classify_category(text: str) -> str:
    """명령어에 포함된 단어를 기반으로 일정의 카테고리를 분류"""
    category_keywords = {
        "회의": ["회의", "미팅", "줌", "온라인회의", "컨퍼런스"],
        "상담": ["상담", "컨설팅", "문의", "점검", "상담예약"],
        "시공": ["시공", "공사", "설치", "작업", "철거"],
        "현장방문": ["현장", "실측", "측량", "방문"],
        "내부업무": ["내부", "테스트", "점검", "확인"]
    }

    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "미정"
