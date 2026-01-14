## Context

FastAPI Launcher 需要从简单的启动器升级为功能完整的进程管理工具。用户反馈需要更灵活的环境管理、更强大的进程控制和实时监控能力。

**约束**：
- 保持向后兼容，现有命令行为不变
- Python 3.10+ 兼容
- Windows 支持基础功能（Gunicorn 和部分信号功能仅 Unix）

## Goals / Non-Goals

### Goals
- 支持多环境配置（dev/prod/staging/test/custom）
- 提供优雅关闭机制，可配置超时时间
- 智能启动模式，自动检测环境
- 手动触发热重载
- 配置模板生成
- 实时监控 TUI 界面
- 可选 Gunicorn 后端支持
- 详细的 Worker 状态展示

### Non-Goals
- 不提供集群/分布式部署功能
- 不替代 Kubernetes/Docker Compose 等编排工具
- 不提供日志聚合/分析功能（仅查看）

## Decisions

### 1. 多环境配置结构

**决定**：在 pyproject.toml 中使用 `[tool.fastapi-launcher.envs.<name>]` 结构

```toml
[tool.fastapi-launcher]
app = "main:app"
host = "127.0.0.1"
port = 8000

[tool.fastapi-launcher.envs.staging]
host = "0.0.0.0"
workers = 2
log_level = "info"

[tool.fastapi-launcher.envs.prod]
host = "0.0.0.0"
workers = 8
log_level = "warning"
```

**理由**：
- 与现有 dev/prod 节区分开，避免命名冲突
- 支持任意自定义环境名
- 继承基础配置，仅覆盖差异值

**替代方案**：
- 使用单独的 `fa.toml` 配置文件 - 增加文件数量，不符合单文件原则
- 使用 YAML 格式 - 需要额外依赖

### 2. Gunicorn 集成策略

**决定**：作为可选后端，通过 `--server gunicorn` 启用

```bash
fa start --server gunicorn --workers 4
```

**Gunicorn 优势**：
1. **进程管理更成熟**：预派生（pre-fork）模型，主进程监控所有 Worker
2. **Worker 自动重启**：Worker 崩溃后自动重启，保证服务高可用
3. **请求限制**：`--max-requests` 防止内存泄漏，Worker 处理一定请求后自动重启
4. **优雅重载**：`--reload` 使用 `SIGHUP` 实现零停机更新
5. **资源隔离**：每个 Worker 独立进程，内存隔离更好

**实现**：
- 生成 Gunicorn 配置并调用 `gunicorn -c` 启动
- 使用 `uvicorn.workers.UvicornWorker` 保持 ASGI 兼容

**替代方案**：
- 替换掉 Uvicorn - 破坏向后兼容
- 使用 Hypercorn - 生态不如 Gunicorn 成熟

### 3. 监控 TUI 实现

**决定**：使用 Textual 库实现，作为可选依赖

```bash
pip install fastapi-launcher[monitor]
fa monitor
```

**理由**：
- Textual 是现代 Python TUI 库，Rich 团队出品
- 与现有 Rich 依赖一致的设计风格
- 支持响应式布局和实时刷新

**替代方案**：
- 使用 curses - 跨平台支持差，Windows 需要额外处理
- 简单 CLI 表格刷新 - 功能有限，无法交互

### 4. 智能启动模式检测顺序

**决定**：按以下优先级检测环境

1. `FA_ENV` 环境变量
2. `PYTHON_ENV` 环境变量
3. `NODE_ENV` 环境变量（兼容全栈项目）
4. `.env` 文件中的 `FA_ENV` 或 `PYTHON_ENV`
5. 启发式检测：
   - 存在 `.git/hooks/pre-commit` → dev
   - 存在 `Dockerfile` 或 `docker-compose.yml` → prod
   - 默认 → dev

### 5. Worker 状态获取

**决定**：
- Uvicorn 模式：通过 psutil 获取子进程信息
- Gunicorn 模式：解析 Gunicorn 的 master/worker 进程树

```python
@dataclass
class WorkerStatus:
    pid: int
    cpuPercent: float
    memoryMb: float
    requestsHandled: int
    status: str  # running/idle/starting
    uptime: float
```

## Risks / Trade-offs

### 风险 1：Gunicorn 依赖体积
- **风险**：增加包体积和安装时间
- **缓解**：作为可选依赖 `[gunicorn]`，不影响基础安装

### 风险 2：Textual 兼容性
- **风险**：TUI 在某些终端模拟器中显示问题
- **缓解**：提供 `--no-tui` 降级为简单输出模式

### 风险 3：Windows 功能降级
- **风险**：Gunicorn 不支持 Windows，信号处理受限
- **缓解**：明确文档说明，提供替代方案建议

### 风险 4：环境检测误判
- **风险**：智能模式可能误判环境
- **缓解**：始终允许显式指定 `--env`，智能模式仅为便捷功能

## Migration Plan

1. **第一阶段**：配置增强（无破坏性）
   - 多环境配置支持
   - 优雅关闭超时
   - `fa init` 命令

2. **第二阶段**：新命令（无破坏性）
   - `fa run` 智能启动
   - `fa reload` 热重载
   - `fa status --verbose`

3. **第三阶段**：高级功能
   - Gunicorn 后端
   - `fa monitor` TUI

## Open Questions

1. `fa monitor` 是否需要支持远程服务器监控？
   - 初步决定：仅支持本地，远程需求可通过 SSH 隧道实现

2. 是否需要支持 Hypercorn 作为另一个后端选项？
   - 初步决定：暂不支持，可作为后续扩展

3. Worker 请求数统计是否需要持久化？
   - 初步决定：仅运行时统计，重启后清零
