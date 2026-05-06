from __future__ import annotations


class ProjectTimelineService:
    def __init__(self, project_repo, scene_repo, storyboard_repo, subject_repo, render_repo, final_repo) -> None:
        self.project_repo = project_repo
        self.scene_repo = scene_repo
        self.storyboard_repo = storyboard_repo
        self.subject_repo = subject_repo
        self.render_repo = render_repo
        self.final_repo = final_repo

    def build(self, project_id: str) -> dict:
        project = self.project_repo.get(project_id)
        if not project:
            raise ValueError("Project not found")
        version = project.get("storyboard_version") or None
        return {
            "project": project,
            "scene": self.scene_repo.latest(project_id),
            "storyboard": self.storyboard_repo.list_by_project(project_id, version),
            "subjects": self.subject_repo.list_by_project(project_id),
            "render_tasks": self.render_repo.list_by_project(project_id),
            "final_video": self.final_repo.latest(project_id),
        }
