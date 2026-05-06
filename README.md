# 智能视频生成平台

这是一个前端基于 Node.js、后端基于 Python 的智能视频生成平台生产化基线版本，已经具备以下能力：

- 创建项目并输入创意
- 生成并审核场景设计
- 生成、编辑并审核分镜脚本
- 抽取主体并生成统一主体素材
- 并行生成镜头视频
- 拼接最终成片并下载
- 查看项目进度与最终产物
- 使用 SQLite 真表结构 + SQL 迁移管理元数据
- 支持文件系统对象存储与 S3/MinIO 对象存储双适配
- 提供 API Key 鉴权、健康检查、Docker Compose 部署基线
- 已接入 DeepSeek 文本模型 `deepseek-reasoner`
- 已接入阿里云 DashScope 图片/视频生成

## 目录结构

- `backend/`：Python 后端服务
- `frontend/`：Node 静态前端服务
- `specs/20260412-ai-video-platform/`：SDD 文档与契约
- `.ttadk/memory/constitution.md`：项目宪章

## 运行端口

- 后端：`http://127.0.0.1:8100`
- 前端：`http://127.0.0.1:3100`
- DeepSeek API：`https://api.deepseek.com`
- MinIO（可选）：`http://127.0.0.1:9000`
- MinIO Console（可选）：`http://127.0.0.1:9001`

## 当前实现说明

当前版本是“生产化基线”，已经具备完整业务链路，并支持真实模型接入：

- 元数据持久化已从 JSON 文件升级为 SQLite 真表结构
- 数据库初始化通过 `backend/src/repositories/migrations/*.sql` 自动迁移
- 对象存储支持：
  - `filesystem`：本地文件系统
  - `s3`：兼容 S3 / MinIO / 阿里云 OSS 兼容网关场景的对象存储
- 文本生成链路：
  - 场景设计：调用 DeepSeek `deepseek-reasoner`
  - 分镜脚本：调用 DeepSeek `deepseek-reasoner`
- 多模态生成链路：
  - 主体图：调用阿里云 DashScope `wan2.7-image`
  - 镜头视频：调用阿里云 DashScope `wan2.7-i2v`
- 当模型或云端服务不可用时，可通过 `ALLOW_MODEL_FALLBACK=true` 自动回退到占位输出，保证联调不断链
- 后端提供 `healthz` / `readyz` 健康检查
- 业务接口默认启用 `X-API-Key` 鉴权

## 环境变量

优先读取仓库根目录 `.env`，示例参考：`.env.example`、`backend/.env.example`、`frontend/.env.example`

关键变量：

- `APP_PORT=8100`
- `FRONTEND_PORT=3100`
- `APP_API_KEY=dev-secret-key-change-me`
- `OBJECT_STORE_PROVIDER=filesystem` 或 `s3`
- `S3_ENDPOINT=http://127.0.0.1:9000`
- `S3_BUCKET=ai-video-platform`
- `S3_ACCESS_KEY=minioadmin`
- `S3_SECRET_KEY=minioadmin`
- `TEXT_PROVIDER=deepseek`
- `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `DEEPSEEK_API_KEY=你的 DeepSeek API Key`
- `DEEPSEEK_TEXT_MODEL=deepseek-reasoner`
- `OLLAMA_BASE_URL=http://127.0.0.1:11434`
- `OLLAMA_TEXT_MODEL=deepseek`
- `DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com`（若使用美国 Virginia 地域，改为 `https://dashscope-us.aliyuncs.com`）
- `DASHSCOPE_API_KEY=你的阿里云 DashScope Key`
- `DASHSCOPE_IMAGE_MODEL=wan2.7-image`
- `DASHSCOPE_VIDEO_MODEL=wan2.7-i2v`
- `ALLOW_MODEL_FALLBACK=true`

## 本地运行

### 1. 配置 DeepSeek 文本模型

在仓库根目录 `.env` 中配置：

```bash
TEXT_PROVIDER=deepseek
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=你的真实密钥
DEEPSEEK_TEXT_MODEL=deepseek-reasoner
```

### 2. 维护本地 `.env`

在仓库根目录 `.env` 中统一维护端口、对象存储、DeepSeek 与 DashScope 配置。后端和前端都会自动读取该文件。

### 3. 启动后端

```bash
make backend
```

### 4. 启动前端

```bash
make frontend
```

### 5. 打开页面

浏览器访问：`http://127.0.0.1:3100`

## Docker Compose 启动

```bash
make docker-up
```

默认会启动：
- `backend`
- `frontend`
- `minio`

停止并清理：

```bash
make docker-down
```

## 推荐体验路径

1. 在首页创建一个项目
2. 进入场景设计页，点击“生成场景设计”
3. 场景审核通过后进入分镜页
4. 在分镜页修改字幕/配音/时长并通过分镜
5. 在渲染页依次点击“生成主体图”“开始渲染”“合成成片”
6. 在成片页下载或查看最终产物

## 自动化验证

运行测试：

```bash
make test
```

当前已覆盖：
- 健康/鉴权规则基础验证
- 完整业务流水线验证
- 模型接线后的回退链路验证

## 关键文件

- `backend/src/integrations/ai_gateway.py`：统一模型网关，屏蔽 DeepSeek / Ollama / DashScope 差异
- `backend/src/integrations/deepseek_client.py`：DeepSeek 文本模型调用
- `backend/src/integrations/ollama_client.py`：Ollama 文本模型调用（可选）
- `backend/src/integrations/dashscope_client.py`：阿里云图片/视频生成调用
- `backend/src/media/object_store.py`：文件系统 / S3 双适配对象存储
- `backend/src/api/app.py`：后端入口与鉴权/健康检查
- `backend/src/repositories/db.py`：SQLite 迁移执行器
- `docker-compose.yml`：生产化基线编排
- `frontend/src/pages/_app.tsx`：前端路由入口

## 已知边界

- 当前环境下若无法访问阿里云 DashScope，系统会根据 `ALLOW_MODEL_FALLBACK` 自动回退为占位素材
- 最终合成阶段仍是可运行的基线拼接实现，不是 ffmpeg 生产级转码链路
- SQLite 适合作为生产化基线或单机部署，不适合作为高并发最终数据库方案
- S3 适配器已支持基础 PUT/GET；桶初始化与权限策略仍建议交给云资源或部署脚本

## 下一步建议

- 将 SQLite 升级为 PostgreSQL
- 将最终合成阶段替换为 ffmpeg / 媒体工作流
- 增加后台任务持久队列与失败重试编排
- 引入更完整的用户认证、权限和告警系统
