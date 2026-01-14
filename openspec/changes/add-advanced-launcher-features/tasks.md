# 任务清单

## ⚠️ 任务执行规则

### 质量门禁
1. **每个模块任务（1-7）完成后**，必须通过对应的测试验收任务
2. **测试覆盖率要求**：新增代码覆盖率 >= 95%
3. **验收标准**：运行 `pytest --cov` 确认覆盖率，所有测试通过
4. **阻塞规则**：当前模块测试未通过前，不得开始下一个模块任务

### 问题记录
- 如果某个任务**无法完成或无法达到 95% 覆盖率**，必须在 `ISSUES.md` 中记录
- 记录格式见下方 [问题记录模板](#问题记录模板)
- 记录后可标记任务为 `[~]`（部分完成）并继续下一任务

### 任务状态标记
- `[ ]` - 待完成
- `[x]` - 已完成并通过验收
- `[~]` - 部分完成（已记录问题）
- `[-]` - 已取消

---

## 1. 配置增强

- [x] 1.1 扩展 `configSchema.py` 支持多环境配置模型
- [x] 1.2 修改 `config.py` 加载 `[tool.fastapi-launcher.envs.<name>]` 配置节
- [x] 1.3 添加 `--env` CLI 选项到 `start` 和 `dev` 命令
- [x] 1.4 添加 `--timeout-graceful-shutdown` 选项
- [x] 1.5 **测试验收**：编写多环境配置单元测试，覆盖率 >= 95%
  - 运行：`pytest tests/test_config.py --cov=fastapi_launcher.config --cov-fail-under=95`

## 2. 新命令实现 - fa init

- [x] 2.1 创建 `init.py` 模块
- [x] 2.2 实现检测现有 pyproject.toml 并追加配置模板
- [x] 2.3 实现 `--env` 选项生成 `.env` 模板
- [x] 2.4 在 `cli.py` 注册 `init` 命令
- [x] 2.5 **测试验收**：编写 `init` 命令测试，覆盖率 >= 95%
  - 运行：`pytest tests/test_init.py --cov=fastapi_launcher.init --cov-fail-under=95`

## 3. 新命令实现 - fa run

- [x] 3.1 创建 `smartMode.py` 模块实现环境检测逻辑
- [x] 3.2 实现环境检测优先级：FA_ENV → PYTHON_ENV → NODE_ENV → .env → 启发式
- [x] 3.3 在 `cli.py` 注册 `run` 命令
- [x] 3.4 **测试验收**：编写环境检测单元测试，覆盖率 >= 95%
  - 运行：`pytest tests/test_smartMode.py --cov=fastapi_launcher.smartMode --cov-fail-under=95`

## 4. 新命令实现 - fa reload

- [x] 4.1 实现发送 SIGHUP 信号给运行中服务器
- [x] 4.2 Windows 下显示不支持警告
- [x] 4.3 在 `cli.py` 注册 `reload` 命令
- [x] 4.4 **测试验收**：编写 `reload` 命令测试，覆盖率 >= 95%
  - 运行：`pytest tests/test_cli.py::test_reload* --cov=fastapi_launcher.cli --cov-fail-under=95`

## 5. Worker 状态展示

- [x] 5.1 扩展 `process.py` 添加 `getWorkerStatuses()` 函数
- [x] 5.2 实现 Uvicorn 模式下通过 psutil 获取子进程信息
- [x] 5.3 为 `status` 命令添加 `--verbose` 选项
- [x] 5.4 实现 Rich 表格展示每个 Worker 状态
- [x] 5.5 **测试验收**：编写 Worker 状态获取测试，覆盖率 >= 95%
  - 运行：`pytest tests/test_process.py --cov=fastapi_launcher.process --cov-fail-under=95`

## 6. Gunicorn 后端支持

- [x] 6.1 在 `launcher.py` 中集成 Gunicorn 后端（内置实现，无需单独模块）
- [x] 6.2 实现 Gunicorn 配置生成（使用 UvicornWorker）
- [x] 6.3 添加 `--server` 选项支持 `uvicorn`/`gunicorn`
- [x] 6.4 添加 `--max-requests` 选项（Gunicorn 特有）
- [x] 6.5 在 pyproject.toml 添加 gunicorn 可选依赖
- [x] 6.6 实现 Gunicorn 模式下的 Worker 状态获取
- [x] 6.7 **测试验收**：编写 Gunicorn 后端测试，覆盖率 >= 95%
  - 运行：`pytest tests/test_launcher.py --cov=fastapi_launcher.launcher --cov-fail-under=95`
  - 注意：Gunicorn 仅支持 Unix，Windows 测试需 mock

## 7. 监控 TUI - fa monitor

- [x] 7.1 添加 textual 可选依赖 `[monitor]`
- [x] 7.2 创建 `monitor.py` TUI 应用
- [x] 7.3 实现实时 CPU/内存/请求数刷新
- [x] 7.4 实现 Worker 列表展示
- [x] 7.5 在 `cli.py` 注册 `monitor` 命令
- [x] 7.6 实现 `--no-tui` 降级模式
- [x] 7.7 **测试验收**：编写监控模块测试，覆盖率 >= 95%
  - 运行：`pytest tests/test_monitor.py --cov=fastapi_launcher.monitor --cov-fail-under=95`

---

## 8. 文档完善

> 文档任务无需测试验收，但需确保示例代码可运行

### 8.1 README 更新
- [x] 8.1.1 添加新命令说明（run/reload/init/monitor）
- [x] 8.1.2 添加多环境配置示例
- [x] 8.1.3 添加 Gunicorn 后端使用说明
- [x] 8.1.4 添加 Worker 状态查看说明

### 8.2 配置文档
- [x] 8.2.1 文档化完整配置项列表（新增项标注）
- [x] 8.2.2 添加 pyproject.toml 多环境配置示例
  ```toml
  [tool.fastapi-launcher]
  app = "main:app"
  
  [tool.fastapi-launcher.envs.staging]
  workers = 2
  log_level = "info"
  
  [tool.fastapi-launcher.envs.prod]
  workers = 8
  server = "gunicorn"
  max_requests = 1000
  timeout_graceful_shutdown = 30
  ```
- [x] 8.2.3 添加 .env 配置示例
  ```bash
  FA_ENV=staging
  FA_HOST=0.0.0.0
  FA_PORT=8000
  FA_WORKERS=4
  FA_SERVER=gunicorn
  FA_TIMEOUT_GRACEFUL_SHUTDOWN=30
  FA_MAX_REQUESTS=1000
  ```
- [x] 8.2.4 添加环境变量优先级说明表
- [x] 8.2.5 添加 `fa init` 生成的配置模板说明

### 8.3 智能启动文档
- [x] 8.3.1 文档化 `fa run` 环境检测逻辑
- [x] 8.3.2 添加检测优先级流程图
- [x] 8.3.3 添加启发式检测规则说明
- [x] 8.3.4 添加常见场景示例（本地开发/Docker/CI）

### 8.4 Gunicorn 配置指南
- [x] 8.4.1 添加 Gunicorn vs Uvicorn 选择指南
- [x] 8.4.2 文档化 Gunicorn 特有配置项
  - `max_requests` - 防止内存泄漏
  - `max_requests_jitter` - 随机重启抖动
  - `worker_class` - Worker 类型选择
- [x] 8.4.3 添加生产环境推荐配置
- [x] 8.4.4 添加 Gunicorn 优势说明（进程管理、自动重启、请求限制）

### 8.5 监控功能文档
- [x] 8.5.1 添加 `fa monitor` 使用说明
- [x] 8.5.2 添加 TUI 快捷键说明
- [x] 8.5.3 添加 `--no-tui` 降级模式说明
- [x] 8.5.4 添加安装可选依赖说明 (`pip install fastapi-launcher[monitor]`)

---

## 9. 最终验收

- [x] 9.1 运行完整测试套件：`pytest --cov=fastapi_launcher --cov-fail-under=95`
- [x] 9.2 确认无遗留 ISSUES.md 中的未解决问题
- [x] 9.3 添加多环境配置集成测试
- [x] 9.4 添加 Gunicorn 后端集成测试（需要 Unix 环境）
- [x] 9.5 添加 Windows 兼容性测试（降级行为）
- [x] 9.6 确认所有文档示例代码可运行

---

## 问题记录模板

当任务无法完成或无法达到 95% 覆盖率时，在 `openspec/changes/add-advanced-launcher-features/ISSUES.md` 中记录：

```markdown
## [任务编号] 任务名称

### 问题描述
[描述遇到的问题]

### 当前状态
- 覆盖率：XX%（目标 95%）
- 未覆盖代码：[列出未覆盖的代码路径]

### 原因分析
[分析无法完成的原因]

### 临时解决方案
[如果有临时方案，描述方案]

### 后续计划
- [ ] [后续修复计划]
- [ ] 预计完成时间：YYYY-MM-DD

### 相关信息
- 相关文件：`src/fastapi_launcher/xxx.py`
- 相关测试：`tests/test_xxx.py`
- 阻塞任务：[列出被阻塞的后续任务]
```
