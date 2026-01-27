# Issues

## Issue #1: 配置文件中的 `daemon = true` 被忽略

### 问题描述

在 `start` 命令中，配置文件（pyproject.toml）中设置的 `daemon = true` 被完全忽略。只有在命令行显式指定 `--daemon` 参数时，守护进程模式才会生效。

### 根本原因

`cli.py` 第 218 行检查的是 CLI 参数 `daemon_mode`，而不是从配置文件加载的 `config.daemon` 值：

```python
# cli.py 第 206-218 行（当前实现）
cliArgs = {
    "app": app_path,
    "host": host,
    "port": port,
    "workers": workers,
    "daemon": daemon_mode,  # ← CLI 参数被放入 cliArgs
    "log_level": log_level,
    ...
}

if daemon_mode:  # ❌ 直接检查 CLI 参数，默认 False
    ...
    daemonize(...)  # 配置文件中的 daemon=true 永远不会到达这里
```

**问题流程：**
1. 用户执行 `fa start --env prod`（没有 `--daemon` 参数）
2. `daemon_mode` = False（CLI 默认值）
3. 第 211 行：`cliArgs["daemon"] = False`
4. 第 218 行：`if daemon_mode:` 为 False，跳过守护进程化
5. 第 224 行：`loadConfig()` 被调用，但守护进程化的判断已经结束了
6. 配置文件中的 `daemon = true` 虽然被加载，但没有被用于决定是否守护进程化

### 行为对比

| 命令 | 配置文件 daemon | CLI --daemon | 当前结果 | 期望结果 |
|------|----------------|--------------|----------|----------|
| `fa start --env prod` | true | 无 | ❌ 前台运行 | ✅ 后台运行 |
| `fa start --env prod --daemon` | true | 有 | ✅ 后台运行 | ✅ 后台运行 |
| `fa start --env prod` | false | 无 | ✅ 前台运行 | ✅ 前台运行 |
| `fa start --env prod --daemon` | false | 有 | ✅ 后台运行 | ✅ 后台运行 |

### 复现步骤

1. 配置 `pyproject.toml`：
   ```toml
   [tool.fastapi-launcher.envs.prod]
   host = "127.0.0.1"
   port = 8020
   daemon = true  # ← 期望生效但被忽略
   ```

2. 启动服务（不带 --daemon）：
   ```bash
   fa start --env prod
   # 期望：后台运行，终端立即返回
   # 实际：前台运行，显示 "Press CTRL+C to quit"
   ```

### 期望行为

配置文件中的 `daemon = true` 应该生效，无需手动指定 `--daemon`。CLI 参数 `--daemon` 应该作为覆盖选项，而不是唯一来源。

### 建议修复

```python
# cli.py start 命令修复

def start(
    ...
    daemon_mode: bool = typer.Option(
        None,  # ← 改为 None，表示未指定
        "--daemon",
        "-d",
        help="Run as daemon (background process)",
    ),
    ...
):
    # 1. 构建 cliArgs，不包含未指定的 daemon
    cliArgs = {
        "app": app_path,
        "host": host,
        "port": port,
        "workers": workers,
        "log_level": log_level,
        ...
    }
    
    # 只有显式指定时才覆盖配置
    if daemon_mode is not None:
        cliArgs["daemon"] = daemon_mode
    
    # 2. 先加载配置（包含环境配置中的 daemon 值）
    config = loadConfig(cliArgs=cliArgs, envName=env)
    
    # 3. 根据最终配置决定是否守护进程化
    if config.daemon:  # ← 使用合并后的配置值
        supported, msg = checkDaemonSupport()
        if not supported:
            printWarningMessage(msg)
        else:
            runtimeDir = config.runtimeDir
            if not runtimeDir.is_absolute():
                runtimeDir = Path.cwd() / runtimeDir
            
            logFile = setupDaemonLogging(runtimeDir)
            pidFile = runtimeDir / "fa.pid"
            
            printInfoMessage(f"Starting daemon... (PID file: {pidFile})")
            daemonize(pidFile=pidFile, logFile=logFile, workDir=Path.cwd())
    
    # 4. 启动服务
    try:
        launch(
            cliArgs=cliArgs, 
            mode=RunMode.PROD, 
            showBanner=not config.daemon,  # ← 使用配置值
            envName=env
        )
    except LaunchError:
        raise typer.Exit(1)
```

### 临时解决方案

在修复之前，必须显式指定 `--daemon` 参数：

```bash
fa start --env prod --daemon
```

### 优先级

高 - 影响生产环境部署

---

## Issue #2: 辅助命令不支持 `--env` 参数导致环境配置不一致

### 问题描述

当使用 `fa start --env prod` 启动服务后，`health`、`status`、`config`、`stop`、`logs` 等辅助命令无法正确识别正在运行的服务，因为这些命令不支持 `--env` 参数，始终使用默认配置。

### 根本原因

辅助命令调用 `loadConfig()` 时没有传入 `envName` 参数：

```python
# cli.py 第 261 行 (stop 命令)
config = loadConfig()  # ❌ 没有传 envName

# cli.py 第 302 行 (restart 命令)
config = loadConfig()  # ❌ 没有传 envName

# cli.py 第 350 行 (status 命令)
config = loadConfig()  # ❌ 没有传 envName

# cli.py 第 418 行 (logs 命令)
config = loadConfig()  # ❌ 没有传 envName

# cli.py 第 470 行 (health 命令)
config = loadConfig()  # ❌ 没有传 envName

# 对比：start 命令正确传入了 envName
config = loadConfig(cliArgs=cliArgs, envName=env)  # ✅
```

### 复现步骤

1. 配置 `pyproject.toml`：
   ```toml
   [tool.fastapi-launcher]
   port = 8000  # 默认端口
   
   [tool.fastapi-launcher.envs.prod]
   port = 8020
   daemon = true
   ```

2. 启动服务：
   ```bash
   fa start --env prod --daemon
   # ℹ Starting daemon... (PID file: runtime/fa.pid)
   # 服务运行在 8020 端口
   ```

3. 检查健康状态：
   ```bash
   fa health
   # 输出: ○ Unhealthy http://127.0.0.1:8000/api/health  ← 检查了错误端口
   # 错误: Connection refused
   ```

4. 查看配置：
   ```bash
   fa config
   # 显示 port = 8000（默认配置）
   # 而不是 port = 8020（prod 环境配置）
   ```

5. 尝试指定环境：
   ```bash
   fa config --env prod
   # 错误: No such option: --env  ← 不支持该参数
   ```

### 期望行为

**方案一：所有辅助命令支持 `--env` 参数**

```bash
fa health --env prod   # 检查 8020 端口
fa status --env prod   # 显示 prod 环境状态
fa config --env prod   # 显示 prod 环境配置
fa stop --env prod     # 停止 prod 环境服务
fa logs --env prod     # 查看 prod 环境日志
```

**方案二：启动时持久化当前环境信息**

1. 启动时将环境信息写入 `runtime/fa.env` 文件：
   ```bash
   fa start --env prod --daemon
   # 自动创建 runtime/fa.env 内容: prod
   ```

2. 其他命令自动读取该文件：
   ```bash
   fa health  # 自动读取 runtime/fa.env，使用 prod 环境配置
   ```

**推荐：两种方案结合**
- 默认读取 `runtime/fa.env`
- 支持 `--env` 参数显式覆盖

### 影响范围

以下命令需要添加 `--env` 参数支持：

| 命令 | 行号 | 当前调用 |
|------|------|----------|
| `stop` | 245-289 | `loadConfig()` |
| `restart` | 292-335 | `loadConfig()` |
| `status` | 338-393 | `loadConfig()` |
| `logs` | 396-440 | `loadConfig()` |
| `health` | 443-490 | `loadConfig()` |
| `config` | 493-496 | `showConfig()` → `loadConfig()` |
| `clean` | 509-565 | `loadConfig()` |
| `reload` | 648-686 | `loadConfig()` |
| `monitor` | 689-735 | `loadConfig()` |

### 建议修复

1. 为所有辅助命令添加 `--env` 参数
2. 修改 `loadConfig()` 调用，传入 `envName` 参数
3. 启动时写入 `runtime/fa.env` 文件记录当前环境
4. 辅助命令优先读取 `runtime/fa.env`，`--env` 参数可覆盖

```python
# 示例：health 命令修复

@app.command()
def health(
    ...
    env: Optional[str] = typer.Option(
        None,
        "--env",
        "-e",
        help="Named environment from pyproject.toml",
    ),
) -> None:
    """Check server health."""
    # 尝试读取持久化的环境
    envName = env or readPersistedEnv()
    
    config = loadConfig(envName=envName)
    ...
```

### 临时解决方案

1. 手动指定端口：
   ```bash
   fa health --port 8020
   ```

2. 使用 curl 直接检查：
   ```bash
   curl http://127.0.0.1:8020/api/health
   ```

3. 查看进程状态：
   ```bash
   ps aux | grep uvicorn
   ss -tlnp | grep 8020
   ```

### 优先级

高 - 影响生产环境部署和监控
