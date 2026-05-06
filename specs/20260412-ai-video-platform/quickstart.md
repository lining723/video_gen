# Quickstart: 智能视频生成平台实现验证

## 1. 阅读顺序
1. 阅读 `spec.md`
2. 阅读 `plan.md`
3. 阅读 `tasks.md`
4. 阅读 `contracts/openapi.yaml`
5. 阅读 `.ttadk/memory/constitution.md`

## 2. 本地运行

### 后端
```bash
APP_PORT=8100 python3 -m backend.src.api.app
```

### 前端
```bash
cd frontend && FRONTEND_PORT=3100 node server.js
```

## 3. Docker 运行

```bash
make docker-up
```

该方式会同时拉起 backend、frontend 与 MinIO。

## 4. 验证链路

1. 创建项目
2. 生成场景设计
3. 审核场景设计为通过
4. 生成分镜脚本
5. 编辑并审核分镜脚本
6. 生成主体素材
7. 启动镜头渲染
8. 触发最终拼接
9. 查看并下载最终产物

## 5. 自动化验证

```bash
make test
```

## 6. 当前实现边界

- 数据库已升级为 SQLite 真表结构 + SQL 迁移
- 对象存储支持文件系统与 S3/MinIO 双模式
- 视频与图片仍为占位文件，不调用真实模型
- 前端仍为零构建 SPA，用于快速验证交互链路

## 7. 本轮验证结果

- 后端代码通过 `python3 -m compileall backend/src`
- 单元测试通过 `python3 -m unittest discover -s backend/tests -v`
- 当前本地链路已验证后端健康检查、鉴权与完整业务流程
