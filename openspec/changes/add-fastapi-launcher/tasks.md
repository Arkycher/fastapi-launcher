# Tasks: FastAPI Launcher 实现

> 每个任务完成后必须立即编写测试，确保覆盖率 >= 75%（初始版本）

## 1. 项目基础设施

- [x] 1.1 完善 pyproject.toml（依赖、entry_points、元数据）
- [x] 1.2 创建 src/fastapi_launcher 目录结构
- [x] 1.3 创建 __init__.py（版本号导出）
- [x] 1.4 创建 py.typed 标记文件
- [x] 1.5 创建 tests/ 目录和 conftest.py
- [x] 1.6 配置 pytest 和 coverage
- [x] 1.7 验证包可安装（uv sync）

## 2. 枚举和基础模型

- [x] 2.1 创建 enums/modeEnum.py（RunMode: DEV/PROD）
- [x] 2.2 创建 enums/logFormatEnum.py（LogFormat: PRETTY/JSON）
- [x] 2.3 创建 schemas/configSchema.py（LauncherConfig Pydantic 模型）
- [x] 2.4 创建 schemas/logSchema.py（LogConfig、AccessLogEntry 模型）
- [x] 2.5 编写测试：test_enums.py
- [x] 2.6 编写测试：test_schemas.py
- [x] 2.7 验证覆盖率 >= 75%

## 3. 配置系统

- [x] 3.1 实现 config.py - 读取 pyproject.toml [tool.fastapi-launcher]
- [x] 3.2 实现 config.py - 加载 .env 文件
- [x] 3.3 实现 config.py - 读取环境变量（FA_ 前缀）
- [x] 3.4 实现 config.py - CLI 参数合并
- [x] 3.5 实现 config.py - 环境配置合并（dev/prod）
- [x] 3.6 实现 config.py - 默认值处理
- [x] 3.7 编写测试：test_config.py - 优先级测试
- [x] 3.8 编写测试：test_config.py - 环境配置测试
- [x] 3.9 编写测试：test_config.py - 边界情况测试
- [x] 3.10 验证覆盖率 >= 75%

## 4. App 自动发现

- [x] 4.1 实现 discover.py - 扫描常见入口点
- [x] 4.2 实现 discover.py - 验证 app 对象存在
- [x] 4.3 实现 discover.py - 多个 app 时的处理
- [x] 4.4 编写测试：test_discover.py
- [x] 4.5 验证覆盖率 >= 75%

## 5. 端口检测

- [x] 5.1 实现 port.py - 检查端口是否被占用
- [x] 5.2 实现 port.py - 获取占用端口的进程信息
- [x] 5.3 实现 port.py - 可选杀掉占用进程
- [x] 5.4 编写测试：test_port.py
- [x] 5.5 验证覆盖率 >= 75%

## 6. 进程管理

- [x] 6.1 实现 process.py - PID 文件写入
- [x] 6.2 实现 process.py - PID 文件读取
- [x] 6.3 实现 process.py - 进程存活检测
- [x] 6.4 实现 process.py - 发送信号（SIGTERM/SIGINT/SIGKILL）
- [x] 6.5 实现 process.py - 获取进程状态（内存、CPU、运行时间）
- [x] 6.6 实现 process.py - 等待进程退出
- [x] 6.7 编写测试：test_process.py - PID 文件测试
- [x] 6.8 编写测试：test_process.py - 信号测试
- [x] 6.9 编写测试：test_process.py - 状态测试
- [x] 6.10 验证覆盖率 >= 75%

## 7. Rich UI 组件

- [x] 7.1 实现 ui.py - 启动信息面板
- [x] 7.2 实现 ui.py - 状态表格
- [x] 7.3 实现 ui.py - 错误信息面板
- [x] 7.4 实现 ui.py - 进度 spinner
- [x] 7.5 实现 ui.py - 日志着色（级别、HTTP 方法）
- [x] 7.6 实现 ui.py - 成功/失败消息
- [x] 7.7 编写测试：test_ui.py（Console 输出捕获）
- [x] 7.8 验证覆盖率 >= 75%

## 8. Launcher 核心

- [x] 8.1 实现 launcher.py - uvicorn 配置构建
- [x] 8.2 实现 launcher.py - 开发模式（reload）
- [x] 8.3 实现 launcher.py - 生产模式（workers）
- [x] 8.4 实现 launcher.py - uvicorn 参数透传
- [x] 8.5 实现 launcher.py - 启动前检查（端口、app）
- [x] 8.6 实现 launcher.py - 信号处理注册
- [x] 8.7 编写测试：test_launcher.py - 配置构建测试
- [x] 8.8 编写测试：test_launcher.py - 模式切换测试
- [x] 8.9 编写测试：test_launcher.py - 参数透传测试
- [x] 8.10 验证覆盖率 >= 75%

## 9. 守护进程模式

- [x] 9.1 实现 daemon.py - Unix 双 fork
- [x] 9.2 实现 daemon.py - setsid 会话分离
- [x] 9.3 实现 daemon.py - 标准流重定向
- [x] 9.4 实现 daemon.py - Windows 平台检测和提示
- [x] 9.5 实现 daemon.py - 日志文件输出
- [x] 9.6 编写测试：test_daemon.py（Unix 平台测试）
- [x] 9.7 编写测试：test_daemon.py（Windows mock 测试）
- [x] 9.8 验证覆盖率 >= 75%

## 10. 日志管理

- [x] 10.1 实现 logs.py - 日志目录自动创建
- [x] 10.2 实现 logs.py - 日志文件写入
- [x] 10.3 实现 logs.py - Pretty 格式化器
- [x] 10.4 实现 logs.py - JSON 格式化器
- [x] 10.5 实现 logs.py - 日志读取（fa logs）
- [x] 10.6 实现 logs.py - 实时追踪（--follow）
- [x] 10.7 实现 accessLog.py - 请求日志记录
- [x] 10.8 实现 accessLog.py - 慢请求标记
- [x] 10.9 实现 accessLog.py - 路径排除
- [x] 10.10 编写测试：test_logs.py - 格式化测试
- [x] 10.11 编写测试：test_logs.py - 文件操作测试
- [x] 10.12 编写测试：test_accessLog.py
- [x] 10.13 验证覆盖率 >= 75%

## 11. 健康检查

- [x] 11.1 实现 health.py - HTTP 健康检查请求
- [x] 11.2 实现 health.py - 响应时间测量
- [x] 11.3 实现 health.py - 状态码判断
- [x] 11.4 实现 health.py - 超时处理
- [x] 11.5 编写测试：test_health.py
- [x] 11.6 验证覆盖率 >= 75%

## 12. 配置和依赖检查

- [x] 12.1 实现 checker.py - 配置验证
- [x] 12.2 实现 checker.py - App 路径验证
- [x] 12.3 实现 checker.py - FastAPI 依赖检查
- [x] 12.4 实现 checker.py - uvicorn 依赖检查
- [x] 12.5 实现 checker.py - 配置显示（fa config）
- [x] 12.6 编写测试：test_checker.py
- [x] 12.7 验证覆盖率 >= 75%

## 13. CLI 命令

- [x] 13.1 实现 cli.py - 创建 Typer app
- [x] 13.2 实现 cli.py - fa dev 命令
- [x] 13.3 实现 cli.py - fa start 命令
- [x] 13.4 实现 cli.py - fa stop 命令
- [x] 13.5 实现 cli.py - fa restart 命令
- [x] 13.6 实现 cli.py - fa status 命令
- [x] 13.7 实现 cli.py - fa logs 命令
- [x] 13.8 实现 cli.py - fa health 命令
- [x] 13.9 实现 cli.py - fa config 命令
- [x] 13.10 实现 cli.py - fa check 命令
- [x] 13.11 实现 cli.py - fa clean 命令
- [x] 13.12 实现 cli.py - --version 回调
- [x] 13.13 实现 cli.py - Shell 补全支持
- [x] 13.14 编写测试：test_cli.py - dev 命令测试
- [x] 13.15 编写测试：test_cli.py - start/stop 命令测试
- [x] 13.16 编写测试：test_cli.py - 其他命令测试
- [x] 13.17 验证覆盖率 >= 75%

## 14. 集成测试

- [x] 14.1 创建测试用 FastAPI 应用
- [x] 14.2 编写集成测试：启动和停止流程
- [x] 14.3 编写集成测试：配置优先级验证
- [x] 14.4 编写集成测试：日志输出验证
- [x] 14.5 编写集成测试：健康检查验证
- [x] 14.6 验证整体覆盖率 >= 75%

## 15. 发布准备

- [x] 15.1 编写 README.md（中英文）
- [x] 15.2 添加 LICENSE（MIT）
- [x] 15.3 创建 .github/workflows/test.yml（CI 测试）
- [x] 15.4 创建 .github/workflows/publish.yml（PyPI 发布）
- [x] 15.5 配置版本号管理
- [x] 15.6 本地完整测试
- [ ] 15.7 发布到 TestPyPI 验证
- [ ] 15.8 发布到 PyPI
