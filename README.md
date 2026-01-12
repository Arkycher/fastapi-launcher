# FastAPI Launcher 🚀

A universal CLI launcher for FastAPI applications with daemon mode, logging, and rich UI.

一个通用的 FastAPI 服务启动器，支持守护进程模式、日志管理和美化终端输出。

## Features | 特性

- 🔥 **Hot Reload** - Development mode with auto-reload | 开发模式自动重载
- 🚀 **Production Ready** - Multi-worker support with uvicorn | 生产模式多 worker 支持
- 👻 **Daemon Mode** - Background process support (Unix) | 守护进程模式
- 📊 **Rich UI** - Beautiful terminal output with Rich | 美化终端输出
- ⚙️ **Flexible Config** - CLI, ENV, .env, pyproject.toml | 灵活的配置系统
- 🏥 **Health Check** - Built-in health monitoring | 内置健康检查
- 📝 **Access Logs** - Request logging with slow request detection | 请求日志和慢请求检测
- 🔍 **Auto Discovery** - Automatically find your FastAPI app | 自动发现 App

## Installation | 安装

```bash
# Using pip
pip install fastapi-launcher

# Using uv
uv add fastapi-launcher
```

## Quick Start | 快速开始

```bash
# Development mode with hot reload
fa dev

# Production mode
fa start --workers 4

# Daemon mode (Unix only)
fa start --daemon

# Check status
fa status

# Stop server
fa stop

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
4. `pyproject.toml` | pyproject.toml
5. Default values (lowest) | 默认值（最低）

### pyproject.toml

```toml
[tool.fastapi-launcher]
app = "main:app"
host = "0.0.0.0"
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
```

### Environment Variables | 环境变量

```bash
FA_APP=main:app
FA_HOST=0.0.0.0
FA_PORT=8000
FA_RELOAD=true
FA_WORKERS=4
FA_LOG_LEVEL=info
FA_LOG_FORMAT=pretty  # or json
FA_DAEMON=false
```

## Commands | 命令

### `fa dev`

Start development server with hot reload.

```bash
fa dev                          # Auto-discover app
fa dev --app main:app           # Specify app
fa dev --port 9000              # Custom port
fa dev --no-reload              # Disable reload
fa dev --reload-dirs src,lib    # Watch specific dirs
```

### `fa start`

Start production server.

```bash
fa start                        # Default 4 workers
fa start --workers 8            # 8 workers
fa start --daemon               # Background mode
fa start --host 0.0.0.0         # Bind to all interfaces
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

### `fa status`

Show server status.

```bash
fa status
# Output:
# ┌─────────────────────────────┐
# │      Server Status          │
# ├──────────┬──────────────────┤
# │ Status   │ ● Running        │
# │ PID      │ 12345            │
# │ URL      │ http://...:8000  │
# │ Uptime   │ 2h 30m 15s       │
# │ Memory   │ 128.5 MB         │
# └──────────┴──────────────────┘
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
