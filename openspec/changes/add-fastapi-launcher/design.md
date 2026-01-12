# Design: FastAPI Launcher

## Context

创建一个通用的 FastAPI 服务启动器，作为独立 Python 包发布到 PyPI。用户通过 `uv add fastapi-launcher` 安装后，可以使用 `fa` 命令管理 FastAPI 服务。

### 约束条件
- Python 3.10+
- 跨平台（Linux/macOS 完整功能，Windows 基础功能）
- 零侵入（不修改用户代码）
- 配置可选（提供合理默认值和自动发现）

## Goals / Non-Goals

### Goals
- 提供统一的 CLI 入口 (`fa` / `fastapi-launcher`)
- 支持开发模式和生产模式
- 支持守护进程模式（Unix）
- 提供美观的终端输出
- 支持灵活的配置系统
- 请求日志记录和查看
- 健康检查集成

### Non-Goals
- 不替代 supervisor/systemd 的完整进程管理
- 不提供负载均衡
- 不提供 Docker/K8s 集成
- 不提供 Web UI

## Decisions

### 1. CLI 框架选择
- **决定**: 使用 Typer + Rich
- **原因**: Typer 提供现代 CLI 体验，Rich 提供美化输出，两者配合良好
- **替代方案**: Click（更成熟但代码更繁琐）、argparse（太基础）

### 2. 配置优先级
- **决定**: CLI > ENV > .env > pyproject.toml > 默认值
- **原因**: 符合 12-factor app 原则，运行时配置优先于静态配置

### 3. 日志系统
- **决定**: 使用标准 logging + Rich Handler
- **原因**: 与 uvicorn 日志系统兼容，无需引入额外依赖
- **替代方案**: loguru（功能更丰富但增加依赖）

### 4. 守护进程实现
- **决定**: Unix 使用双 fork + setsid，Windows 不支持
- **原因**: 最可靠的 Unix daemon 实现方式
- **替代方案**: subprocess.Popen（更简单但进程关联性问题）

### 5. 请求日志
- **决定**: 拦截 uvicorn access log 并增强
- **原因**: 复用现有机制，减少侵入性

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  fa dev | fa start | fa stop | fa status | fa logs | ...   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      Config Layer                            │
│  CLI Args → ENV → .env → pyproject.toml → Defaults          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                       Core Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Launcher │ │ Process  │ │  Daemon  │ │   Logs   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Health  │ │   Port   │ │ Discover │ │ Checker  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                        UI Layer                              │
│  Rich Panels | Tables | Progress | Spinners | Colors        │
└─────────────────────────────────────────────────────────────┘
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| `fa` 命令名冲突 | 同时注册 `fastapi-launcher` 完整命令 |
| Windows 功能受限 | 明确文档说明，提示使用 nssm |
| uvicorn 版本兼容 | 指定最低版本，测试多版本 |
| 配置复杂性 | 提供 `fa config` 命令显示生效配置 |

## File Structure

```
src/fastapi_launcher/
├── __init__.py         # 版本号
├── py.typed            # 类型提示标记
├── cli.py              # CLI 入口
├── config.py           # 配置解析
├── launcher.py         # uvicorn 启动
├── process.py          # 进程管理
├── port.py             # 端口检测
├── daemon.py           # 守护进程（Unix）
├── logs.py             # 日志管理
├── accessLog.py        # 请求日志
├── health.py           # 健康检查
├── ui.py               # Rich 输出
├── discover.py         # App 自动发现
├── checker.py          # 配置/依赖检查
├── schemas/
│   ├── configSchema.py # 配置模型
│   └── logSchema.py    # 日志模型
└── enums/
    ├── modeEnum.py     # 运行模式
    └── logFormatEnum.py # 日志格式
```

## Dependencies

```toml
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "uvicorn[standard]>=0.30.0",
    "httpx>=0.27.0",        # 健康检查
    "psutil>=6.0.0",        # 进程监控、端口检测
    "pydantic>=2.0.0",      # 配置模型
    "python-dotenv>=1.0.0", # .env 文件支持
]
```

## Error Handling Strategy

| 场景 | 处理方式 |
|------|----------|
| 配置错误 | 清晰提示缺失/无效字段 |
| 端口冲突 | 显示占用进程信息，提供解决建议 |
| App 未找到 | 列出尝试的路径，提示配置方法 |
| 权限不足 | 提示使用 sudo 或检查文件权限 |
| 依赖缺失 | 提示安装 FastAPI/uvicorn |

## Version Management

- 使用 `__version__` 导出版本号
- 支持 `fa --version` 查看
- 使用 git tag 触发 PyPI 发布

## Runtime Directory Structure

用户项目安装后的目录结构：

```
your-fastapi-project/
├── pyproject.toml              # [tool.fastapi-launcher] 配置
├── .env                        # 环境变量（可选）
├── src/
│   └── main.py                 # FastAPI app
└── runtime/                    # 运行时目录（自动创建）
    ├── fa.pid                  # PID 文件
    └── logs/
        ├── fa.log              # 应用日志
        ├── access.log          # 请求日志
        └── error.log           # 错误日志
```

## Open Questions

- 是否需要支持 Gunicorn 作为替代 worker？（当前决定：不支持，保持简单）
- 是否需要支持配置文件热重载？（当前决定：不支持，重启服务）
