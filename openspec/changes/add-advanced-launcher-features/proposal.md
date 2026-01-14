# Change: 增强 FastAPI Launcher 高级功能

## Why

当前 FastAPI Launcher 仅支持基础的 dev/prod 两种模式，缺乏灵活的环境配置、进程管理和监控能力。生产环境部署需要更强大的进程管理器（Gunicorn）、优雅关闭、动态监控等企业级功能。

## What Changes

### 1. 多环境配置支持
- 支持 `fa start --env staging/test/custom` 环境选择
- pyproject.toml 支持 `[tool.fastapi-launcher.staging]` 等自定义环境配置节
- 环境继承基础配置并覆盖特定值

### 2. 优雅关闭增强
- 新增 `--timeout-graceful-shutdown` 选项
- 支持配置关闭超时时间
- 确保进行中的请求在关闭前完成

### 3. 智能启动模式
- 新增 `fa run` 命令，自动检测环境选择 dev/prod 模式
- 基于 `FA_ENV`、`NODE_ENV`、`.env` 文件自动判断
- 简化日常使用命令

### 4. 热重载触发
- 新增 `fa reload` 命令，手动触发热重载
- 发送 SIGHUP 信号给运行中的服务器
- 仅在开发模式下有效

### 5. 配置初始化
- 新增 `fa init` 命令，在现有 pyproject.toml 基础上添加配置模板
- 支持 `fa init --env` 生成 .env 模板
- 智能检测现有配置，避免覆盖

### 6. 动态监控
- 新增 `fa monitor` 命令，实时监控服务器状态
- 类似 `htop` 的 TUI 界面，显示 CPU、内存、请求数
- 支持每个 Worker 的详细状态展示

### 7. **BREAKING** Gunicorn 后端支持
- 新增 `--server gunicorn` 选项
- Gunicorn + UvicornWorker 组合，提供更强的进程管理
- 支持 Worker 自动重启、最大请求数限制

### 8. Worker 状态展示
- `fa status --verbose` 显示每个 Worker 详情
- 展示每个 Worker 的 PID、CPU、内存、请求数
- Gunicorn 模式下更精确的 Worker 管理

## Impact

- **Affected specs**: cli, config, launcher, process（新增 monitor）
- **Affected code**: 
  - `cli.py` - 新增 run/reload/init/monitor 命令
  - `config.py` - 多环境配置支持
  - `launcher.py` - Gunicorn 后端集成
  - `process.py` - Worker 状态获取
  - 新增 `monitor.py` - TUI 监控模块
  - 新增 `gunicorn.py` - Gunicorn 配置生成
- **Dependencies**: 
  - 新增可选依赖 `gunicorn>=22.0.0`
  - 可选 TUI 库 `textual>=0.50.0`（用于 monitor）

## Migration

- 现有命令保持兼容
- `fa dev` / `fa start` 行为不变
- Gunicorn 为可选后端，默认仍使用 Uvicorn
