from __future__ import annotations

from backend.src.workers.queue import executor


def submit_task(func, *args, **kwargs):
    return executor.submit(func, *args, **kwargs)


def submit_keyframe_generation(pipeline, project: dict, shot: dict, subject: dict) -> str:
    """
    提交关键帧生成任务到后台队列

    Args:
        pipeline: KeyframePipeline 实例
        project: 项目数据
        shot: 镜头数据
        subject: 主体数据

    Returns:
        任务ID
    """
    future = executor.submit(pipeline.generate_keyframes_for_shot, shot, subject, project)
    return str(id(future))

