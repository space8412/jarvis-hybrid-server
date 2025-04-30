def handle_intent(data):
    from tools.intent_identifier import identify_intent
    from tools.session_manager import create_session
    from tools.create_handler import handle_create

    user_input = data.get('text', '')
    user_id = data.get('user_id', 'default_user')
    intent = identify_intent(user_input)
    session_id = create_session(user_id)

    if intent == 'create':
        return handle_create(user_input, user_id, session_id)
    else:
        from flask import jsonify
        return jsonify({"success": False, "message": "현재는 등록만 지원됩니다."})
