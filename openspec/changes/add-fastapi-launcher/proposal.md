# Change: 创建 FastAPI Launcher 通用启动器

## Why

FastAPI 项目缺少统一的服务管理工具。每个项目都需要自己编写启动脚本、处理进程管理、配置日志等重复工作。需要一个通用的 CLI 工具来标准化这些操作，提高开发效率。

## What Changes

- 创建完整的 Python 包项目结构
- 实现配置系统（四层优先级合并）
- 实现进程管理（PID 文件、信号处理、端口检测）
- 实现 uvicorn 启动逻辑（开发/生产模式）
- 实现守护进程模式（仅 Unix）
- 实现日志管理（pretty/json 格式、请求日志）
- 实现健康检查
- 实现 Rich 美化 UI
- 实现完整 CLI 命令集（dev/start/stop/restart/status/logs/health/config/check/clean）
- 发布到 PyPI

## Impact

- Affected specs: cli, config, process, launcher, daemon, logs, health, ui
- Affected code: 全新项目，创建 `src/fastapi_launcher/` 目录下所有模块
- 测试覆盖率要求: >= 95%
