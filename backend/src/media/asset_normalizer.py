from __future__ import annotations

from pathlib import Path

from backend.src.settings.logging import log_event


def is_probably_mp4(payload: bytes) -> bool:
    if len(payload) < 12:
        return False
    return b'ftyp' in payload[:32]


def is_text_payload(payload: bytes) -> bool:
    try:
        payload.decode('utf-8')
    except UnicodeDecodeError:
        return False
    return True


def _fs_path(storage_path: str, object_root: Path) -> Path | None:
    if not storage_path.startswith('fs/'):
        return None
    return object_root / storage_path.replace('fs/', '', 1)


def _normalize_entry(storage_path: str, object_root: Path) -> str:
    path = _fs_path(storage_path, object_root)
    if not path or path.suffix.lower() != '.mp4' or not path.exists():
        return storage_path

    payload = path.read_bytes()
    if is_probably_mp4(payload) or not is_text_payload(payload):
        return storage_path

    normalized = path.with_suffix('.txt')
    normalized.write_bytes(payload)
    path.unlink()
    relative = normalized.relative_to(object_root)
    return f'fs/{relative.as_posix()}'


def normalize_filesystem_media_paths(db, object_root: Path) -> None:
    render_rows = db.fetchall('SELECT id, render_path FROM render_tasks WHERE render_path LIKE ?', ('fs/%.mp4',))
    final_rows = db.fetchall('SELECT id, storage_path FROM final_videos WHERE storage_path LIKE ?', ('fs/%.mp4',))

    updated_render = 0
    for row in render_rows:
        normalized = _normalize_entry(row['render_path'], object_root)
        if normalized != row['render_path']:
            db.execute('UPDATE render_tasks SET render_path = ? WHERE id = ?', (normalized, row['id']))
            updated_render += 1

    updated_final = 0
    for row in final_rows:
        normalized = _normalize_entry(row['storage_path'], object_root)
        if normalized != row['storage_path']:
            db.execute('UPDATE final_videos SET storage_path = ? WHERE id = ?', (normalized, row['id']))
            updated_final += 1

    if updated_render or updated_final:
        log_event('media.assets.normalized', render_tasks=updated_render, final_videos=updated_final)
