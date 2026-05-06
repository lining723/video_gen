ALTER TABLE render_tasks ADD COLUMN provider_name TEXT NOT NULL DEFAULT '';
ALTER TABLE render_tasks ADD COLUMN provider_task_id TEXT NOT NULL DEFAULT '';
ALTER TABLE render_tasks ADD COLUMN progress_message TEXT NOT NULL DEFAULT '';
ALTER TABLE render_tasks ADD COLUMN last_polled_at TEXT NOT NULL DEFAULT '';
