from __future__ import annotations

from threading import Event, Lock, Thread

from backend.src.settings.logging import log_event


class RenderStatusPoller:
    def __init__(self, render_repo, render_pipeline, interval_seconds: float = 5.0) -> None:
        self.render_repo = render_repo
        self.render_pipeline = render_pipeline
        self.interval_seconds = max(interval_seconds, 1.0)
        self._stop_event = Event()
        self._started = False
        self._thread: Thread | None = None
        self._lock = Lock()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
            self._thread = Thread(target=self._run_loop, name='render-status-poller', daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=1.0)

    def poll_once(self) -> list[dict]:
        results = []
        for task in self.render_repo.list_active_provider_tasks():
            try:
                updated = self.render_pipeline.poll_render_task(task['id'])
            except Exception as error:
                log_event('render.poller.task_failed', task_id=task.get('id'), provider_task_id=task.get('provider_task_id'), error=str(error))
                continue
            if updated:
                results.append(updated)
        return results

    def refresh_task(self, task_id: str) -> dict | None:
        return self.render_pipeline.poll_render_task(task_id)

    def _run_loop(self) -> None:
        while not self._stop_event.wait(self.interval_seconds):
            self.poll_once()
