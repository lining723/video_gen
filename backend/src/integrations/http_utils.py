from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderHttpError(RuntimeError):
    def __init__(self, provider: str, method: str, url: str, message: str, status_code: int | None = None, response_text: str = '') -> None:
        self.provider = provider
        self.method = method
        self.url = url
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        detail = f'{provider} {method} {url} failed: {message}'
        if status_code is not None:
            detail += f' (status={status_code})'
        if response_text:
            detail += f' body={response_text[:500]}'
        super().__init__(detail)

    def to_dict(self) -> dict:
        return {
            'provider': self.provider,
            'method': self.method,
            'url': self.url,
            'message': self.message,
            'status_code': self.status_code,
            'response_text': self.response_text,
        }



def http_json(method: str, url: str, headers: dict | None = None, body: dict | None = None, timeout: int = 60, provider: str = 'http'):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
    request = Request(url, data=data, method=method, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read().decode('utf-8')
            return json.loads(payload) if payload else {}
    except HTTPError as error:
        response_text = error.read().decode('utf-8', errors='replace') if error.fp else ''
        raise ProviderHttpError(provider, method, url, str(error.reason), status_code=error.code, response_text=response_text) from error
    except URLError as error:
        raise ProviderHttpError(provider, method, url, str(error.reason)) from error
    except json.JSONDecodeError as error:
        raise ProviderHttpError(provider, method, url, f'invalid json response: {error}') from error



def http_bytes(url: str, timeout: int = 60, provider: str = 'http') -> bytes:
    request = Request(url, method='GET')
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as error:
        response_text = error.read().decode('utf-8', errors='replace') if error.fp else ''
        raise ProviderHttpError(provider, 'GET', url, str(error.reason), status_code=error.code, response_text=response_text) from error
    except URLError as error:
        raise ProviderHttpError(provider, 'GET', url, str(error.reason)) from error
