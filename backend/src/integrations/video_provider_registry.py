"""
视频生成提供商注册中心

管理多个视频生成提供商，支持模型路由。
"""
from __future__ import annotations

from typing import Optional

from .video_provider_base import VideoProvider, VideoModelInfo


class VideoProviderRegistry:
    """视频生成提供商注册中心"""

    def __init__(self) -> None:
        self._providers: dict[str, VideoProvider] = {}
        self._model_to_provider: dict[str, str] = {}
        self._default_model: str = ""

    def register(self, provider: VideoProvider) -> None:
        """注册提供商"""
        if not provider.enabled:
            return

        self._providers[provider.provider_id] = provider

        # 建立模型ID到提供商的映射
        for model in provider.get_available_models():
            self._model_to_provider[model.id] = provider.provider_id
            # 同时支持不带前缀的模型类型作为key
            self._model_to_provider[model.model_type] = provider.provider_id

    def unregister(self, provider_id: str) -> None:
        """注销提供商"""
        provider = self._providers.pop(provider_id, None)
        if provider:
            # 清理模型映射
            for model in provider.get_available_models():
                self._model_to_provider.pop(model.id, None)
                self._model_to_provider.pop(model.model_type, None)

    def get_provider(self, provider_id: str) -> Optional[VideoProvider]:
        """获取提供商"""
        return self._providers.get(provider_id)

    def get_provider_for_model(self, model_id: str) -> Optional[VideoProvider]:
        """根据模型ID获取提供商"""
        # 先尝试完整ID
        provider_id = self._model_to_provider.get(model_id)
        if provider_id:
            return self._providers.get(provider_id)

        # 尝试去掉前缀
        for prefix in ["dashscope-", "volcengine-", "runway-"]:
            if model_id.startswith(prefix):
                model_type = model_id[len(prefix):]
                provider_id = self._model_to_provider.get(model_type)
                if provider_id:
                    return self._providers.get(provider_id)

        return None

    def get_all_models(self) -> list[dict]:
        """返回所有可用模型"""
        models = []
        for provider in self._providers.values():
            for model in provider.get_available_models():
                models.append(model.to_dict())
        return models

    def get_all_providers(self) -> list[dict]:
        """返回所有提供商"""
        return [
            {
                "id": p.provider_id,
                "name": p.provider_name,
                "enabled": p.enabled,
                "models": [m.to_dict() for m in p.get_available_models()],
            }
            for p in self._providers.values()
        ]

    def get_model_info(self, model_id: str) -> Optional[VideoModelInfo]:
        """获取模型信息"""
        provider = self.get_provider_for_model(model_id)
        if provider:
            # 提取模型类型
            model_type = model_id
            for prefix in ["dashscope-", "volcengine-", "runway-"]:
                if model_type.startswith(prefix):
                    model_type = model_type[len(prefix):]
                    break
            return provider.get_model_info(model_type)
        return None

    def set_default_model(self, model_id: str) -> None:
        """设置默认模型"""
        self._default_model = model_id

    @property
    def default_model(self) -> str:
        """获取默认模型"""
        if self._default_model:
            return self._default_model
        # 返回第一个可用模型
        models = self.get_all_models()
        if models:
            return models[0]["id"]
        return ""

    def is_valid_model(self, model_id: str) -> bool:
        """检查模型ID是否有效"""
        return model_id in self._model_to_provider
