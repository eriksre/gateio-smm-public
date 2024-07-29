import time
import hashlib
import hmac
from typing import Dict, Optional

# TODO: add support for futures
# rename to be only for get + post req's. should have more consistent naming, as WS requires different auth

class AuthGateio:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def gen_sign(self, method: str, url: str, query_string: Optional[str] = None, payload_string: Optional[str] = None) -> Dict[str, str]:
        t = time.time()
        m = hashlib.sha512()
        m.update((payload_string or "").encode('utf-8'))
        hashed_payload = m.hexdigest()
        s = f'{method}\n{url}\n{query_string or ""}\n{hashed_payload}\n{t}'
        sign = hmac.new(self.api_secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return {'KEY': self.api_key, 'Timestamp': str(t), 'SIGN': sign}

    def get_headers(self, method: str, url: str, query_string: Optional[str] = None, payload_string: Optional[str] = None) -> Dict[str, str]:
        headers = self.gen_sign(method, url, query_string, payload_string)
        headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})
        return headers

