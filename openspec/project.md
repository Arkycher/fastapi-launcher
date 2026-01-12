# Project Context

## Purpose

fastapi-launcher 是一个通用的 FastAPI 服务启动器，提供美观的 CLI 界面来管理 FastAPI 服务的启动、停止和监控。通过 PyPI 分发，任何 FastAPI 项目都可以通过 `fa` 命令快速启动服务。

## Tech Stack

- Python 3.10+
- Typer (CLI 框架)
- Rich (终端美化)
- uvicorn (ASGI 服务器)
- Pydantic (配置验证)
- httpx (HTTP 客户端)
- psutil (进程管理)
- python-dotenv (.env 支持)
- pytest (测试框架)
- pytest-cov (覆盖率)

## Project Conventions

### Code Style

- 使用 camelCase 命名变量、函数和文件名
- 使用 PascalCase 命名类
- 使用 UPPER_SNAKE_CASE 命名常量和枚举值
- 所有函数必须有类型注解
- 使用 docstring 记录公共 API

### Architecture Patterns

- src layout: 源码在 `src/fastapi_launcher/`
- Pydantic models 分为 `schemas/`（API 模型）和内部模型
- Enums 放在 `enums/` 目录
- 每个模块职责单一

### Testing Strategy

- 使用 pytest 进行测试
- 测试覆盖率要求 >= 95%
- 每实现一个功能模块，必须立即编写对应测试
- 测试文件放在 `tests/` 目录

### Git Workflow

- Commit message 使用中文
- 类型前缀：feat/fix/refactor/docs/test/chore
- 示例：`feat: 添加配置解析模块`

## Domain Context

- 用户通过 `fa` 或 `fastapi-launcher` 命令使用
- 配置优先级：CLI 参数 > 环境变量 > .env > pyproject.toml > 默认值
- 支持开发模式（热重载）和生产模式（多 worker）
- 守护进程模式仅支持 Unix 系统

## Important Constraints

- Python 3.10+ 兼容
- Linux/macOS: 完整功能
- Windows: 基础功能（不支持 daemon 模式）
- 作为独立包发布到 PyPI

## External Dependencies

- uvicorn: ASGI 服务器
- 目标项目需要安装 FastAPI
