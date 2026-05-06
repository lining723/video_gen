"""
模型配置 API 路由

提供获取可用模型列表的接口。
"""
from __future__ import annotations


def register_model_routes(router, context) -> None:
    """注册模型相关路由"""

    def list_video_models(_request, _params):
        """GET /api/models/video - 列出所有可用的视频模型"""
        registry = context.video_provider_registry
        return 200, {
            "ok": True,
            "providers": registry.get_all_providers(),
            "models": registry.get_all_models(),
            "default_model": registry.default_model,
        }

    def list_text_models(_request, _params):
        """GET /api/models/text - 列出可用的文本模型"""
        from backend.src.settings.config import settings

        models = []
        provider = str(settings.text_provider or '').strip().lower()

        if provider == 'deepseek' or not provider:
            models.append({
                "id": settings.deepseek_text_model,
                "name": "DeepSeek Reasoner" if "reasoner" in settings.deepseek_text_model else "DeepSeek",
                "provider_id": "deepseek",
                "provider_name": "DeepSeek",
            })
        if provider == 'ollama' or not provider:
            models.append({
                "id": settings.ollama_text_model,
                "name": settings.ollama_text_model.title(),
                "provider_id": "ollama",
                "provider_name": "Ollama",
            })

        return 200, {
            "ok": True,
            "models": models,
            "default_model": settings.default_text_model,
        }

    def list_image_models(_request, _params):
        """GET /api/models/image - 列出可用的图片模型"""
        from backend.src.settings.config import settings

        return 200, {
            "ok": True,
            "models": [
                {
                    "id": settings.dashscope_image_model,
                    "name": "Wan 2.7 图像生成",
                    "provider_id": "dashscope",
                    "provider_name": "阿里云灵积",
                }
            ],
            "default_model": settings.dashscope_image_model,
        }

    def get_model_info(_request, params):
        """GET /api/models/{model_type}/{model_id} - 获取模型详情"""
        model_type = params.get('model_type')
        model_id = params.get('model_id')

        if model_type == 'video':
            registry = context.video_provider_registry
            model_info = registry.get_model_info(model_id)
            if model_info:
                return 200, {"ok": True, "model": model_info.to_dict()}
            return 404, {"ok": False, "error": f"Model not found: {model_id}"}

        return 404, {"ok": False, "error": f"Unknown model type: {model_type}"}

    router.add("GET", "/api/models/video", list_video_models)
    router.add("GET", "/api/models/text", list_text_models)
    router.add("GET", "/api/models/image", list_image_models)
    router.add("GET", "/api/models/{model_type}/{model_id}", get_model_info)
