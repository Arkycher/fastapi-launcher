# FastAPI Launcher 🚀

A universal CLI launcher for FastAPI applications with daemon mode, logging, and rich UI.

一个通用的 FastAPI 服务启动器，支持守护进程模式、日志管理和美化终端输出。

## Features | 特性

- 🔥 **Hot Reload** - Development mode with auto-reload | 开发模式自动重载
- 🚀 **Production Ready** - Multi-worker support with uvicorn/gunicorn | 生产模式多 worker 支持
- 👻 **Daemon Mode** - Background process support (Unix) | 守护进程模式
- 📊 **Rich UI** - Beautiful terminal output with Rich | 美化终端输出
- ⚙️ **Flexible Config** - CLI, ENV, .env, pyproject.toml | 灵活的配置系统
- 🌍 **Multi-Environment** - staging/qa/prod custom environments | 多环境配置支持
- 🏥 **Health Check** - Built-in health monitoring | 内置健康检查
- 📝 **Access Logs** - Request logging with slow request detection | 请求日志和慢请求检测
- 🔍 **Auto Discovery** - Automatically find your FastAPI app | 自动发现 App
- 🎯 **Smart Mode** - Auto-detect dev/prod based on environment | 智能模式检测
- 📡 **Real-time Monitor** - TUI monitor for server status | 实时 TUI 监控
- 🦄 **Gunicorn Backend** - Optional Gunicorn for enhanced process management | 可选 Gunicorn 后端

## Installation | 安装

```bash
# Using pip
pip install fastapi-launcher

# With optional Gunicorn support
pip install fastapi-launcher[gunicorn]

# With TUI monitor
pip install fastapi-launcher[monitor]

# All extras
pip install fastapi-launcher[all]

# Using uv
uv add fastapi-launcher
```

## Quick Start | 快速开始

```bash
# Initialize config in pyproject.toml
fa init

# Smart mode - auto-detect dev/prod
fa run

# Development mode with hot reload
fa dev

# Production mode
fa start --workers 4

# Start with specific environment
fa start --env staging

# Gunicorn backend (Unix only)
fa start --server gunicorn --workers 8

# Daemon mode (Unix only)
fa start --daemon

# Check status (detailed worker info)
fa status --verbose

# Stop server
fa stop

# Trigger hot reload
fa reload

# Real-time monitor
fa monitor

# View logs
fa logs --follow

# Health check
fa health

# Show configuration
fa config

# Check dependencies
fa check
```

## Configuration | 配置

### Configuration Priority | 配置优先级

1. CLI arguments (highest) | CLI 参数（最高）
2. Environment variables (`FA_` prefix) | 环境变量
3. `.env` file | .env 文件
4. `pyproject.toml [tool.fastapi-launcher.envs.<name>]` (if --env specified) | 命名环境配置
5. `pyproject.toml [tool.fastapi-launcher]` | 基础配置
6. Default values (lowest) | 默认值（最低）

### pyproject.toml

```toml
[tool.fastapi-launcher]
app = "main:app"
host = "127.0.0.1"
port = 8000
log_level = "info"

# Development mode overrides
[tool.fastapi-launcher.dev]
reload = true
log_level = "debug"

# Production mode overrides
[tool.fastapi-launcher.prod]
workers = 4
log_format = "json"
daemon = false

# Named environments (use with --env)
[tool.fastapi-launcher.envs.staging]
host = "0.0.0.0"
workers = 2
log_level = "info"

[tool.fastapi-launcher.envs.qa]
host = "0.0.0.0"
workers = 1
log_level = "debug"

[tool.fastapi-launcher.envs.prod]
host = "0.0.0.0"
workers = 8
server = "gunicorn"
max_requests = 1000
timeout_graceful_shutdown = 30
log_level = "warning"
```

### Environment Variables | 环境变量

```bash
# Environment selection
FA_ENV=staging

# Server configuration
FA_APP=main:app
FA_HOST=0.0.0.0
FA_PORT=8000
FA_RELOAD=true
FA_WORKERS=4

# Server backend (uvicorn/gunicorn)
FA_SERVER=uvicorn

# Graceful shutdown
FA_TIMEOUT_GRACEFUL_SHUTDOWN=10

# Gunicorn-specific (when FA_SERVER=gunicorn)
FA_MAX_REQUESTS=1000
FA_MAX_REQUESTS_JITTER=100

# Logging
FA_LOG_LEVEL=info
FA_LOG_FORMAT=pretty  # or json
FA_DAEMON=false
```

## Commands | 命令

### `fa init`

Initialize FastAPI Launcher configuration.

```bash
fa init                         # Add config to pyproject.toml
fa init --env                   # Also generate .env.example
fa init --force                 # Overwrite existing config
```

### `fa run`

Smart start - auto-detect dev/prod mode based on environment.

```bash
fa run                          # Detect environment and start
# Detection priority:
# 1. FA_ENV environment variable
# 2. PYTHON_ENV environment variable
# 3. NODE_ENV environment variable
# 4. .env file
# 5. Heuristics (Dockerfile → prod, .git/hooks/pre-commit → dev)
```

### `fa dev`

Start development server with hot reload.

```bash
fa dev                          # Auto-discover app
fa dev --app main:app           # Specify app
fa dev --port 9000              # Custom port
fa dev --no-reload              # Disable reload
fa dev --reload-dirs src,lib    # Watch specific dirs
fa dev --env staging            # Use staging environment
```

### `fa start`

Start production server.

```bash
fa start                        # Default 4 workers
fa start --workers 8            # 8 workers
fa start --daemon               # Background mode
fa start --host 0.0.0.0         # Bind to all interfaces
fa start --env staging          # Use staging environment
fa start --server gunicorn      # Use Gunicorn backend
fa start --max-requests 1000    # Worker restart after N requests
fa start --timeout-graceful-shutdown 30  # Graceful shutdown timeout
```

### `fa stop`

Stop running server.

```bash
fa stop                         # Graceful shutdown
fa stop --force                 # Force kill
fa stop --timeout 30            # Custom timeout
```

### `fa restart`

Restart server.

```bash
fa restart                      # Stop + Start
fa restart --timeout 10         # Custom stop timeout
```

### `fa reload`

Trigger hot reload on running server (Unix only).

```bash
fa reload                       # Send SIGHUP to server
```

### `fa status`

Show server status.

```bash
fa status                       # Basic status
fa status --verbose             # Include worker details

# Output:
# ┌─────────────────────────────┐
# │      Server Status          │
# ├──────────┬──────────────────┤
# │ Status   │ ● Running        │
# │ PID      │ 12345            │
# │ URL      │ http://...:8000  │
# │ Uptime   │ 2h 30m 15s       │
# │ Memory   │ 128.5 MB         │
# │ Workers  │ 4                │
# └──────────┴──────────────────┘
```

### `fa monitor`

Real-time monitoring with TUI interface.

```bash
fa monitor                      # TUI mode (requires textual)
fa monitor --no-tui             # Simple CLI refresh mode
fa monitor --refresh 0.5        # Custom refresh interval
```

### `fa logs`

View server logs.

```bash
fa logs                         # Last 100 lines
fa logs -n 50                   # Last 50 lines
fa logs --follow                # Tail mode
fa logs --type access           # Access logs
fa logs --type error            # Error logs
```

### `fa health`

Check server health.

```bash
fa health                       # Default endpoint
fa health --path /ready         # Custom endpoint
fa health --timeout 10          # Custom timeout
```

### `fa config`

Show current configuration.

```bash
fa config
# Output shows merged config from all sources
```

### `fa check`

Check dependencies and configuration.

```bash
fa check
# ✓ FastAPI is installed
# ✓ uvicorn is installed
# ✓ Configuration is valid
# ✓ App path is valid: main:app
```

### `fa clean`

Clean runtime files.

```bash
fa clean                        # Interactive
fa clean --yes                  # Skip confirmation
fa clean --logs                 # Only log files
```

## Project Structure | 项目结构

After running `fa start`, a runtime directory is created:

```
your-project/
├── pyproject.toml
├── main.py
└── runtime/
    ├── fa.pid          # PID file
    └── logs/
        ├── fa.log      # Application log
        ├── access.log  # Request log
        └── error.log   # Error log
```

## App Auto-Discovery | 自动发现

FastAPI Launcher will look for your app in these locations:

1. `main.py` → `main:app`
2. `app.py` → `app:app`
3. `api.py` → `api:app`
4. `server.py` → `server:app`
5. `src/main.py` → `src.main:app`

Supported variable names: `app`, `application`, `api`

## License | 许可证

MIT License

## Contributing | 贡献

Contributions are welcome! Please feel free to submit issues and pull requests.

欢迎贡献！请随时提交 issues 和 pull requests。
