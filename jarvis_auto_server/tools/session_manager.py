import uuid, json, os
import redis
from datetime import datetime

REDIS_URL = os.environ.get('REDIS_URL')
redis_client = redis.from_url(REDIS_URL)
SESSION_EXPIRY = 3600

def create_session(user_id):
    session_id = str(uuid.uuid4())
    redis_client.setex(f"jarvis:session:{session_id}", SESSION_EXPIRY, json.dumps({
        'user_id': user_id,
        'created_at': datetime.now().isoformat()
    }))
    return session_id
