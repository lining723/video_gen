from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from backend.src.integrations.http_utils import http_bytes
from backend.src.settings.config import OBJECT_ROOT, settings


class FileObjectStore:
    def __init__(self) -> None:
        self.root = Path(OBJECT_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)

    def _target_path(self, project_id: str, name: str) -> Path:
        directory = self.root / project_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory / name

    def save_text(self, project_id: str, name: str, content: str) -> str:
        path = self._target_path(project_id, name)
        path.write_text(content, encoding='utf-8')
        return f'fs/{project_id}/{name}'

    def save_bytes(self, project_id: str, name: str, content: bytes, content_type: str = 'application/octet-stream') -> str:
        path = self._target_path(project_id, name)
        path.write_bytes(content)
        return f'fs/{project_id}/{name}'

    def save_from_url(self, project_id: str, name: str, url: str, content_type: str = 'application/octet-stream') -> str:
        return self.save_bytes(project_id, name, http_bytes(url), content_type=content_type)

    def read_bytes(self, storage_path: str) -> bytes:
        relative = storage_path.replace('fs/', '', 1)
        path = self.root / relative
        return path.read_bytes()


@dataclass(slots=True)
class S3Config:
    endpoint: str
    region: str
    bucket: str
    access_key: str
    secret_key: str


class S3ObjectStore:
    def __init__(self, config: S3Config) -> None:
        self.config = config
        parsed = urlparse(config.endpoint)
        self.host = parsed.netloc
        self.ensure_bucket()

    def ensure_bucket(self) -> None:
        canonical_uri = f'/{self.config.bucket}'
        try:
            headers = self._headers('HEAD', canonical_uri, b'', 'application/octet-stream')
            request = Request(f'{self.config.endpoint}{canonical_uri}', method='HEAD', headers=headers)
            with urlopen(request, timeout=10) as response:
                response.read()
            return
        except Exception:
            headers = self._headers('PUT', canonical_uri, b'', 'application/octet-stream')
            request = Request(f'{self.config.endpoint}{canonical_uri}', data=b'', method='PUT', headers=headers)
            with urlopen(request, timeout=10) as response:
                response.read()

    def _sign(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def _signature_key(self, date_stamp: str) -> bytes:
        k_date = self._sign(('AWS4' + self.config.secret_key).encode('utf-8'), date_stamp)
        k_region = self._sign(k_date, self.config.region)
        k_service = self._sign(k_region, 's3')
        return self._sign(k_service, 'aws4_request')

    def _headers(self, method: str, canonical_uri: str, payload: bytes, content_type: str) -> dict:
        now = datetime.now(UTC)
        amz_date = now.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = now.strftime('%Y%m%d')
        payload_hash = hashlib.sha256(payload).hexdigest()
        canonical_headers = (
            f'content-type:{content_type}\n'
            f'host:{self.host}\n'
            f'x-amz-content-sha256:{payload_hash}\n'
            f'x-amz-date:{amz_date}\n'
        )
        signed_headers = 'content-type;host;x-amz-content-sha256;x-amz-date'
        canonical_request = '\n'.join([
            method,
            canonical_uri,
            '',
            canonical_headers,
            signed_headers,
            payload_hash,
        ])
        credential_scope = f'{date_stamp}/{self.config.region}/s3/aws4_request'
        string_to_sign = '\n'.join([
            'AWS4-HMAC-SHA256',
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode('utf-8')).hexdigest(),
        ])
        signature = hmac.new(self._signature_key(date_stamp), string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        authorization = (
            'AWS4-HMAC-SHA256 '
            f'Credential={self.config.access_key}/{credential_scope}, '
            f'SignedHeaders={signed_headers}, Signature={signature}'
        )
        return {
            'Content-Type': content_type,
            'Host': self.host,
            'X-Amz-Content-Sha256': payload_hash,
            'X-Amz-Date': amz_date,
            'Authorization': authorization,
        }

    def _key(self, project_id: str, name: str) -> str:
        return f"{quote(project_id, safe='-_.~')}/{quote(name, safe='-_.~')}"

    def _put(self, project_id: str, name: str, payload: bytes, content_type: str) -> str:
        key = self._key(project_id, name)
        canonical_uri = f'/{self.config.bucket}/{key}'
        headers = self._headers('PUT', canonical_uri, payload, content_type)
        request = Request(f'{self.config.endpoint}{canonical_uri}', data=payload, method='PUT', headers=headers)
        with urlopen(request, timeout=10) as response:
            response.read()
        return f's3/{self.config.bucket}/{key}'

    def save_text(self, project_id: str, name: str, content: str) -> str:
        return self._put(project_id, name, content.encode('utf-8'), 'text/plain; charset=utf-8')

    def save_bytes(self, project_id: str, name: str, content: bytes, content_type: str = 'application/octet-stream') -> str:
        return self._put(project_id, name, content, content_type)

    def save_from_url(self, project_id: str, name: str, url: str, content_type: str = 'application/octet-stream') -> str:
        return self.save_bytes(project_id, name, http_bytes(url), content_type=content_type)

    def read_bytes(self, storage_path: str) -> bytes:
        _, bucket, *rest = storage_path.split('/')
        key = '/'.join(rest)
        canonical_uri = f'/{bucket}/{key}'
        payload = b''
        headers = self._headers('GET', canonical_uri, payload, 'application/octet-stream')
        request = Request(f'{self.config.endpoint}{canonical_uri}', method='GET', headers=headers)
        with urlopen(request, timeout=10) as response:
            return response.read()


class ObjectStore:
    def __init__(self) -> None:
        if settings.object_store_provider == 's3':
            self.backend = S3ObjectStore(
                S3Config(
                    endpoint=settings.s3_endpoint,
                    region=settings.s3_region,
                    bucket=settings.s3_bucket,
                    access_key=settings.s3_access_key,
                    secret_key=settings.s3_secret_key,
                )
            )
        else:
            self.backend = FileObjectStore()

    def save_text(self, project_id: str, name: str, content: str) -> str:
        return self.backend.save_text(project_id, name, content)

    def save_bytes(self, project_id: str, name: str, content: bytes, content_type: str = 'application/octet-stream') -> str:
        return self.backend.save_bytes(project_id, name, content, content_type=content_type)

    def save_from_url(self, project_id: str, name: str, url: str, content_type: str = 'application/octet-stream') -> str:
        return self.backend.save_from_url(project_id, name, url, content_type=content_type)

    def read_bytes(self, storage_path: str) -> bytes:
        return self.backend.read_bytes(storage_path)
