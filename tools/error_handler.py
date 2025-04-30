from flask import jsonify

def handle_error(e):
    return jsonify({'success': False, 'message': f'서버 오류: {str(e)}'})
