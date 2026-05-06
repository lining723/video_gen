from __future__ import annotations

import json
from urllib.error import URLError

from .http_utils import http_json


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout

    def generate_json(self, prompt: str, schema_hint: str, model: str | None = None) -> dict:
        active_model = model or self.model
        payload = {
            'model': active_model,
            'prompt': f'{prompt}\n\n请严格输出 JSON，格式要求：{schema_hint}',
            'format': 'json',
            'stream': False,
        }
        response = http_json('POST', f'{self.base_url}/api/generate', {'Content-Type': 'application/json'}, payload, timeout=self.timeout)
        raw = response.get('response', '{}')
        if isinstance(raw, dict):
            return raw
        return json.loads(raw)

    def is_available(self) -> bool:
        try:
            http_json('POST', f'{self.base_url}/api/generate', {'Content-Type': 'application/json'}, {
                'model': self.model,
                'prompt': 'ping',
                'stream': False,
            }, timeout=15)
            return True
        except Exception:
            return False
