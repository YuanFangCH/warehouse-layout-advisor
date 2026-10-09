# 仓储布局决策参谋

这是一个面向仓储布局分析的全栈决策支持 WebUI 原型。系统通过对话澄清业务
目标，将需求转换为结构化分析条件，执行评估流程，并展示可追溯的证据、推荐
结果和版本记录。

前端负责交互和可视化，FastAPI 后端负责工作流状态、业务规则、版本管理、
持久化和模型网关。评估模型作为可替换的后端服务接入，默认使用确定性的
Mock 网关，不需要外部网络。

仅用于参赛演示，不具备任何实际价值

## 功能

- 多轮澄清改造范围、优先级、预算、性能底线、风险偏好和分析周期。
- 使用场景版本和乐观并发检查，避免条件覆盖。
- 在后台线程执行评估，并通过 Server-Sent Events 推送进度。
- 展示证据、KPI、洞察、推荐、采纳和重算结果。
- 支持 OpenAI 兼容的 Chat Completions 接口，也支持离线 Mock 模式。
- 使用 SQLite 持久化，首次启动自动建表并写入演示数据。

## 目录结构

```text
frontend/
  src/api/             HTTP 与 SSE 客户端
  src/components/      通用交互与分析组件
  src/features/        场景版本对比
  src/pages/           项目总览与场景工作台
  src/stores/          跨组件 UI 状态
  tests/               Vitest 与 Testing Library 测试

backend/
  app/api/             FastAPI 路由
  app/domain/          澄清、翻译、解释与推荐服务
  app/orchestration/   评估任务、工作流与事件发布
  app/adapters/        Mock 与 OpenAI 兼容模型网关
  app/models/          Pydantic Schema、ORM 实体与枚举
  app/persistence/     SQLite、Repository 与迁移
  tests/               Pytest 集成测试与工作流测试
```

## 环境要求

- Python 3.11 或更高版本
- Node.js 18 或更高版本
- npm 9 或更高版本

## 启动后端

安装依赖：

```powershell
cd backend
python -m pip install -r requirements.txt
```

启动 API：

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

也可以从仓库根目录启动：

```powershell
$env:PYTHONPATH='backend'
python -m uvicorn app.main:app --port 8000
```

API 地址为 `http://127.0.0.1:8000`，健康检查接口为 `GET /api/health`。

## 启动前端

安装依赖并启动开发服务器：

```powershell
cd frontend
npm install
npm run dev
```

打开 `http://127.0.0.1:5173`。Vite 会将 `/api` 代理到
`http://127.0.0.1:8000`。

如需访问其他 API 地址，请在启动 Vite 前设置 `VITE_API_BASE_URL`。

## 模型配置

未设置 `OPENCODE_API_KEY` 时，后端使用内置 Mock 网关。该模式结果确定，
不依赖外部网络。

如需接入 OpenAI 兼容的 Chat Completions 接口，请设置：

```powershell
$env:OPENCODE_API_KEY='your-api-key'
$env:OPENCODE_API_URL='https://opencode.ai/zen/go/v1/chat/completions'
$env:OPENCODE_MODEL='deepseek-v4-flash'
$env:OPENCODE_FORCE_IPV4='1'
```

所有配置只从环境变量读取，不要提交真实密钥。变量名称参见
`backend/.env.example`。

## 测试

后端测试：

```powershell
$env:PYTHONPATH='backend'
python -m pytest backend/tests -q
```

前端测试与构建：

```powershell
cd frontend
npm test
npm run build
```

## API 概览

```text
GET    /api/health

GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}

GET    /api/projects/{project_id}/scenarios
POST   /api/projects/{project_id}/scenarios
GET    /api/scenarios/{scenario_id}
PATCH  /api/scenarios/{scenario_id}
GET    /api/scenarios/{scenario_id}/versions
GET    /api/scenarios/{scenario_id}/events

GET    /api/scenarios/{scenario_id}/messages
POST   /api/scenarios/{scenario_id}/messages
GET    /api/scenarios/{scenario_id}/clarifications
POST   /api/scenarios/{scenario_id}/clarifications/{question_id}/answer
POST   /api/scenarios/{scenario_id}/confirm

POST   /api/scenarios/{scenario_id}/evaluations
GET    /api/evaluations/{evaluation_id}
GET    /api/evaluations/{evaluation_id}/events
GET    /api/evaluations/{evaluation_id}/stream
GET    /api/evaluations/{evaluation_id}/evidence
GET    /api/evaluations/{evaluation_id}/insights
GET    /api/evaluations/{evaluation_id}/recommendation

POST   /api/scenarios/{scenario_id}/approve
POST   /api/scenarios/{scenario_id}/revise
```

错误响应使用统一结构：

```json
{
  "error": {
    "code": "SCENARIO_VERSION_CONFLICT",
    "message": "当前场景已产生新版本",
    "details": {
      "server_version": 5,
      "client_version": 4
    }
  }
}
```

## 数据存储

本项目使用 SQLite 做本地持久化。首次启动时会在
`backend/data/warehouse_decision.db` 自动创建数据库

## 许可证

MIT
