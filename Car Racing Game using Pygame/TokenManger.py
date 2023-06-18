import json
import uuid
import time
from datetime import datetime, timedelta
import os


class TokenManager:
    def __init__(self, token_lifetime_minutes=30):
        self.token_lifetime = timedelta(minutes=token_lifetime_minutes)

    def generate_token(self):
        token = {
            "uuid": str(uuid.uuid4()),
            "timestamp": int(time.time())  # Unix timestamp
        }

        with open('token.json', 'w') as f:
            json.dump(token, f)

        return token

    def is_token_expired(self, token):
        token_timestamp = token['timestamp']
        token_expiration_time = token_timestamp + \
            int(self.token_lifetime.total_seconds())

        return int(time.time()) > token_expiration_time

    def get(self):
        if not os.path.exists('token.json'):
            return self.generate_token()

        with open('token.json', 'r') as f:
            token = json.load(f)

        if not token or 'uuid' not in token or 'timestamp' not in token or self.is_token_expired(token):
            return self.generate_token()

        return token
