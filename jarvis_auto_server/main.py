from flask import Flask, request, jsonify
from tools.intent_handler import handle_intent
from tools.error_handler import handle_error

app = Flask(__name__)

@app.route('/trigger', methods=['POST'])
def trigger():
    try:
        data = request.json
        response = handle_intent(data)
        return response
    except Exception as e:
        return handle_error(e)

if __name__ == '__main__':
    app.run(debug=True)

# WSGI
app = app
