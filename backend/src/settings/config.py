from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = ROOT / 'backend'
DATA_ROOT = BACKEND_ROOT / 'data'
MEDIA_ROOT = DATA_ROOT / 'media'
CACHE_ROOT = MEDIA_ROOT / 'cache'
OBJECT_ROOT = MEDIA_ROOT / 'object_store'
DB_ROOT = DATA_ROOT / 'db'
LOG_ROOT = DATA_ROOT / 'logs'
SQLITE_PATH = DB_ROOT / 'app.sqlite3'
ENV_PATH = ROOT / '.env'


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value[:1] == value[-1:] and value[:1] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


load_env_file(ENV_PATH)


@dataclass(slots=True)
class Settings:
    env: str = os.getenv('APP_ENV', 'production')
    host: str = os.getenv('APP_HOST', '127.0.0.1')
    port: int = int(os.getenv('APP_PORT', '8100'))
    frontend_url: str = os.getenv('FRONTEND_URL', 'http://127.0.0.1:3100')
    api_prefix: str = '/api'
    api_key: str = os.getenv('APP_API_KEY', 'dev-secret-key-change-me')
    scene_max_shots: int = int(os.getenv('SCENE_MAX_SHOTS', '3'))
    shot_duration_limit: int = int(os.getenv('SHOT_DURATION_LIMIT', '10'))
    render_workers: int = int(os.getenv('RENDER_WORKERS', '4'))
    retry_limit: int = int(os.getenv('RETRY_LIMIT', '3'))

    object_store_provider: str = os.getenv('OBJECT_STORE_PROVIDER', 'filesystem')
    s3_endpoint: str = os.getenv('S3_ENDPOINT', 'http://127.0.0.1:9000')
    s3_region: str = os.getenv('S3_REGION', 'us-east-1')
    s3_bucket: str = os.getenv('S3_BUCKET', 'ai-video-platform')
    s3_access_key: str = os.getenv('S3_ACCESS_KEY', 'minioadmin')
    s3_secret_key: str = os.getenv('S3_SECRET_KEY', 'minioadmin')

    ollama_base_url: str = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    ollama_text_model: str = os.getenv('OLLAMA_TEXT_MODEL', 'deepseek')
    ollama_timeout: int = int(os.getenv('OLLAMA_TIMEOUT', '120'))
    text_provider: str = os.getenv('TEXT_PROVIDER', 'deepseek')
    deepseek_base_url: str = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    deepseek_api_key: str = os.getenv('DEEPSEEK_API_KEY', '')
    deepseek_text_model: str = os.getenv('DEEPSEEK_TEXT_MODEL', 'deepseek-reasoner')
    deepseek_timeout: int = int(os.getenv('DEEPSEEK_TIMEOUT', '120'))

    dashscope_base_url: str = os.getenv('DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com')
    dashscope_api_key: str = os.getenv('DASHSCOPE_API_KEY', '')
    dashscope_image_model: str = os.getenv('DASHSCOPE_IMAGE_MODEL', 'wan2.7-image')
    dashscope_video_model: str = os.getenv('DASHSCOPE_VIDEO_MODEL', 'wan2.7-i2v')
    dashscope_image_size: str = os.getenv('DASHSCOPE_IMAGE_SIZE', '1024*1024')
    dashscope_video_resolution: str = os.getenv('DASHSCOPE_VIDEO_RESOLUTION', '720P')
    dashscope_video_ratio: str = os.getenv('DASHSCOPE_VIDEO_RATIO', '16:9')
    dashscope_timeout: int = int(os.getenv('DASHSCOPE_TIMEOUT', '300'))
    dashscope_poll_interval: float = float(os.getenv('DASHSCOPE_POLL_INTERVAL', '3'))
    dashscope_poll_timeout: int = int(os.getenv('DASHSCOPE_POLL_TIMEOUT', '360'))
    render_status_poll_interval: float = float(os.getenv('RENDER_STATUS_POLL_INTERVAL', '5'))
    allow_model_fallback: bool = os.getenv('ALLOW_MODEL_FALLBACK', 'true').lower() in {'1', 'true', 'yes', 'on'}

    @property
    def default_text_model(self) -> str:
        provider = str(self.text_provider or '').strip().lower()
        if provider == 'deepseek':
            return self.deepseek_text_model
        return self.ollama_text_model


def ensure_dirs() -> None:
    for path in [DATA_ROOT, MEDIA_ROOT, CACHE_ROOT, OBJECT_ROOT, DB_ROOT, LOG_ROOT]:
        path.mkdir(parents=True, exist_ok=True)


settings = Settings()
ensure_dirs()
