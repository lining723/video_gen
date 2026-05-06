from __future__ import annotations

import json
import re

from .http_utils import http_json


class DeepSeekClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _extract_text(self, content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                    continue
                if isinstance(item, dict) and item.get('type') == 'text':
                    chunks.append(str(item.get('text') or ''))
            return ''.join(chunks)
        return str(content or '')

    def _extract_json(self, text: str) -> dict:
        candidate = text.strip()
        if not candidate:
            raise ValueError('DeepSeek returned empty content')
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        fenced = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', candidate, flags=re.IGNORECASE)
        if fenced:
            body = fenced.group(1).strip()
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return parsed

        first_obj = candidate.find('{')
        last_obj = candidate.rfind('}')
        if first_obj != -1 and last_obj > first_obj:
            parsed = json.loads(candidate[first_obj:last_obj + 1])
            if isinstance(parsed, dict):
                return parsed

        raise ValueError('DeepSeek did not return a valid JSON object')

    def generate_json(self, prompt: str, schema_hint: str, model: str | None = None) -> dict:
        if not self.api_key:
            raise ValueError('DEEPSEEK_API_KEY is not configured')
        active_model = model or self.model
        payload = {
            'model': active_model,
            'messages': [
                {'role': 'system', 'content': 'You are a JSON API. Return only valid JSON without markdown.'},
                {'role': 'user', 'content': f'{prompt}\n\n请严格输出 JSON，格式要求：{schema_hint}'},
            ],
            'temperature': 0.2,
            'stream': False,
        }
        response = http_json(
            'POST',
            f'{self.base_url}/chat/completions',
            {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            payload,
            timeout=self.timeout,
            provider='deepseek',
        )
        choices = response.get('choices') or []
        if not choices:
            raise ValueError(f'DeepSeek response missing choices: {response}')
        message = choices[0].get('message') or {}
        content = self._extract_text(message.get('content'))
        return self._extract_json(content)
