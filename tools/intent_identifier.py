def identify_intent(text):
    text = text.lower()
    for intent, keywords in {
        'create': ['등록', '추가', '만들어', '잡아', '넣어', '생성'],
    }.items():
        if any(k in text for k in keywords):
            return intent
    return 'create'
