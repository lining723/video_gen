# Research: 智能视频生成平台

## Decision 1: 前端采用 React/Next.js + TypeScript
- **Decision**: 使用 React/Next.js 作为前端框架，TypeScript 作为默认语言。
- **Rationale**: 适合项目列表、审核页、分镜编辑器、任务进度页等复杂交互场景；便于服务端渲染与前后端契约协同。
- **Alternatives considered**: 纯 React SPA；Vue。放弃原因是需要兼顾工程组织、页面路由和企业场景扩展性。

## Decision 2: 后端采用 FastAPI + 异步任务队列
- **Decision**: 使用 FastAPI 作为在线 API 层，并引入任务队列处理长耗时生成任务。
- **Rationale**: FastAPI 适合构建契约清晰的 Python 服务；异步队列更适合视频生成、拼接和重试控制。
- **Alternatives considered**: Flask + 自建线程池；Django。放弃原因是类型约束、异步任务模型和接口文档生成不如 FastAPI 直接。

## Decision 3: 使用 PostgreSQL + 对象存储 + 本地缓存目录
- **Decision**: 元数据进 PostgreSQL，图片/视频进对象存储，镜头复用结果落本地或挂载缓存目录。
- **Rationale**: 三类数据访问模式不同；分层后更便于追踪、复用和控制成本。
- **Alternatives considered**: 全量落本地文件系统；全量落对象存储。放弃原因是分别不利于检索和低成本缓存命中。

## Decision 4: 拼接方案采用 FFmpeg 标准管线
- **Decision**: 使用 FFmpeg 统一处理镜头拼接、字幕轨、配音轨和导出。
- **Rationale**: FFmpeg 在音视频处理场景成熟稳定，适合标准化输出和自动化执行。
- **Alternatives considered**: 自研媒体处理流程；依赖第三方在线拼接服务。放弃原因是可控性或成本不佳。

## Decision 5: 缓存策略使用强一致组合键
- **Decision**: 缓存键由镜头内容哈希、主体图版本、模型版本、渲染配置组成。
- **Rationale**: 能最大限度避免错误复用并确保模型升级后自动失效。
- **Alternatives considered**: 仅基于镜头文本缓存。放弃原因是无法识别素材版本和模型变化。

## Decision 6: 契约优先组织开发
- **Decision**: 先定义 `openapi.yaml`，再推进前后端并行开发。
- **Rationale**: 当前仓库尚未落代码，契约优先有利于降低联调风险。
- **Alternatives considered**: 先写后端再补接口文档。放弃原因是容易造成前后端认知漂移。
