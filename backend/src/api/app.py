from __future__ import annotations

import json
import mimetypes
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socket import timeout as SocketTimeout
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.src.api.middleware.request_context import build_request_context
from backend.src.api.routes import register_all
from backend.src.app_context import AppContext
from backend.src.settings.config import SQLITE_PATH, settings
from backend.src.settings.logging import configure_logging, log_event


class Router:
    def __init__(self) -> None:
        self.routes: list[tuple[str, re.Pattern, object]] = []

    def add(self, method: str, pattern: str, handler) -> None:
        regex = re.sub(r'\{([^}]+)\}', r'(?P<\1>[^/]+)', pattern)
        self.routes.append((method.upper(), re.compile(f'^{regex}$'), handler))

    def match(self, method: str, path: str):
        for route_method, pattern, handler in self.routes:
            match = pattern.match(path)
            if route_method == method.upper() and match:
                return handler, match.groupdict()
        return None, None


class RequestHandler(BaseHTTPRequestHandler):
    router = Router()
    context = None
    auth_exempt_prefixes = {'/healthz', '/readyz', '/media/'}

    def _send(self, status: int, payload: dict | bytes, content_type: str = 'application/json', extra_headers: dict | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8') if content_type == 'application/json' else payload
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', settings.frontend_url)
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,PUT,OPTIONS')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, SocketTimeout):
            return

    def _read_json(self) -> dict:
        length = int(self.headers.get('Content-Length', '0'))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode('utf-8'))
        except json.JSONDecodeError as error:
            raise ValueError(f'Invalid JSON body: {error.msg}') from error

    def _is_auth_exempt(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.auth_exempt_prefixes)

    def _check_api_key(self, path: str) -> bool:
        if self._is_auth_exempt(path):
            return True
        return self.headers.get('X-API-Key', '') == settings.api_key

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', settings.frontend_url)
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,PUT,OPTIONS')
        self.end_headers()

    def do_GET(self):
        self._handle('GET')

    def do_POST(self):
        self._handle('POST')

    def do_PUT(self):
        self._handle('PUT')

    def _handle(self, method: str) -> None:
        parsed = urlparse(self.path)
        if parsed.path == '/healthz':
            self._send(200, {'ok': True, 'status': 'healthy', 'env': settings.env})
            return
        if parsed.path == '/readyz':
            self._send(200, {'ok': True, 'status': 'ready', 'database': str(SQLITE_PATH.exists()), 'object_store': settings.object_store_provider})
            return
        if parsed.path.startswith('/media/'):
            self._serve_media(parsed.path)
            return
        if not self._check_api_key(parsed.path):
            self._send(401, {'ok': False, 'error': 'Unauthorized'})
            return
        try:
            request = {
                'method': method,
                'path': parsed.path,
                'query': parse_qs(parsed.query),
                'json': self._read_json() if method in {'POST', 'PUT'} else {},
                'context': build_request_context(),
            }
            handler, params = self.router.match(method, parsed.path)
            if not handler:
                self._send(404, {'ok': False, 'error': 'Not found'})
                return
            status, payload = handler(request, params)
            log_event('request.completed', method=method, path=parsed.path, trace_id=request['context']['trace_id'], status=status)
            self._send(status, payload)
        except Exception as error:
            log_event('request.failed', method=method, path=parsed.path, error=str(error))
            self._send(400, {'ok': False, 'error': str(error)})

    def _serve_media(self, path: str) -> None:
        storage_path = unquote(path.replace('/media/', '', 1))
        if self.context is None:
            self._send(503, {'ok': False, 'error': 'Media service unavailable'})
            return
        try:
            body = self.context.object_store.read_bytes(storage_path)
        except Exception:
            self._send(404, {'ok': False, 'error': 'Media not found'})
            return
        content_type, _ = mimetypes.guess_type(storage_path)
        content_type = content_type or 'application/octet-stream'
        range_header = self.headers.get('Range', '')
        headers = {'Accept-Ranges': 'bytes'}

        if range_header.startswith('bytes='):
            try:
                start, end = parse_byte_range(range_header, len(body))
            except ValueError:
                self._send(416, b'', content_type, extra_headers={'Accept-Ranges': 'bytes', 'Content-Range': f'bytes */{len(body)}'})
                return
            chunk = body[start:end + 1]
            headers['Content-Range'] = f'bytes {start}-{end}/{len(body)}'
            self._send(206, chunk, content_type, extra_headers=headers)
            return

        self._send(200, body, content_type, extra_headers=headers)


def parse_byte_range(range_header: str, size: int) -> tuple[int, int]:
    spec = range_header.replace('bytes=', '', 1).split(',', 1)[0].strip()
    if '-' not in spec:
        raise ValueError('Invalid range header')
    start_text, end_text = spec.split('-', 1)
    if not start_text and not end_text:
        raise ValueError('Invalid range header')

    if not start_text:
        suffix = int(end_text)
        if suffix <= 0:
            raise ValueError('Invalid suffix range')
        start = max(size - suffix, 0)
        end = size - 1
    else:
        start = int(start_text)
        end = int(end_text) if end_text else size - 1

    if start < 0 or end < start or start >= size:
        raise ValueError('Range outside payload')
    return start, min(end, size - 1)


def create_server() -> ThreadingHTTPServer:
    configure_logging()
    RequestHandler.router = Router()
    RequestHandler.context = AppContext()
    register_all(RequestHandler.router, RequestHandler.context)
    return ThreadingHTTPServer((settings.host, settings.port), RequestHandler)


if __name__ == '__main__':
    server = create_server()
    print(f'Backend running on http://{settings.host}:{settings.port}')
    try:
        server.serve_forever()
    finally:
        if RequestHandler.context is not None:
            RequestHandler.context.close()
