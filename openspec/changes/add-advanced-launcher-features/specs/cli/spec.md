## ADDED Requirements

### Requirement: Smart Run Command

The system SHALL provide `fa run` command for intelligent environment-aware startup.

#### Scenario: Auto-detect development environment
- **WHEN** user runs `fa run`
- **AND** FA_ENV is not set
- **AND** .git/hooks/pre-commit exists
- **THEN** server SHALL start in development mode with reload enabled

#### Scenario: Auto-detect production environment
- **WHEN** user runs `fa run`
- **AND** FA_ENV=production is set
- **THEN** server SHALL start in production mode with workers

#### Scenario: Environment variable priority
- **WHEN** FA_ENV=staging is set
- **AND** NODE_ENV=development is set
- **THEN** FA_ENV SHALL take precedence and staging config SHALL be used

### Requirement: Reload Command

The system SHALL provide `fa reload` command to trigger hot reload.

#### Scenario: Trigger reload on running server
- **WHEN** user runs `fa reload`
- **AND** server is running in dev mode
- **THEN** SIGHUP signal SHALL be sent to server process
- **AND** message "Reload triggered" SHALL be displayed

#### Scenario: Reload on stopped server
- **WHEN** user runs `fa reload`
- **AND** no server is running
- **THEN** error "No server is running" SHALL be displayed

#### Scenario: Reload on Windows
- **WHEN** user runs `fa reload` on Windows
- **THEN** warning "Reload command is not supported on Windows" SHALL be displayed

### Requirement: Init Command

The system SHALL provide `fa init` command to initialize configuration.

#### Scenario: Initialize in new project
- **WHEN** user runs `fa init`
- **AND** pyproject.toml exists without [tool.fastapi-launcher] section
- **THEN** [tool.fastapi-launcher] section SHALL be appended
- **AND** template configuration SHALL be added

#### Scenario: Initialize with existing config
- **WHEN** user runs `fa init`
- **AND** [tool.fastapi-launcher] section already exists
- **THEN** message "Configuration already exists" SHALL be displayed
- **AND** no changes SHALL be made unless --force is specified

#### Scenario: Generate env template
- **WHEN** user runs `fa init --env`
- **THEN** .env.example file SHALL be created with FA_ prefixed variables

### Requirement: Monitor Command

The system SHALL provide `fa monitor` command for real-time status monitoring.

#### Scenario: Start monitor TUI
- **WHEN** user runs `fa monitor`
- **AND** textual is installed
- **AND** server is running
- **THEN** TUI interface SHALL display real-time stats

#### Scenario: Monitor without TUI dependency
- **WHEN** user runs `fa monitor`
- **AND** textual is not installed
- **THEN** error "Install monitor extra: pip install fastapi-launcher[monitor]" SHALL be displayed

#### Scenario: Monitor fallback mode
- **WHEN** user runs `fa monitor --no-tui`
- **THEN** simple CLI output SHALL refresh every second

### Requirement: Environment Selection Option

The system SHALL support `--env` option for environment selection.

#### Scenario: Start with staging environment
- **WHEN** user runs `fa start --env staging`
- **AND** [tool.fastapi-launcher.envs.staging] section exists
- **THEN** staging configuration SHALL override base config

#### Scenario: Unknown environment
- **WHEN** user runs `fa start --env unknown`
- **AND** [tool.fastapi-launcher.envs.unknown] does not exist
- **THEN** error "Environment 'unknown' not found in configuration" SHALL be displayed

### Requirement: Server Backend Selection

The system SHALL support `--server` option to select server backend.

#### Scenario: Use Gunicorn backend
- **WHEN** user runs `fa start --server gunicorn`
- **AND** gunicorn is installed
- **THEN** Gunicorn SHALL be used with UvicornWorker

#### Scenario: Gunicorn not installed
- **WHEN** user runs `fa start --server gunicorn`
- **AND** gunicorn is not installed
- **THEN** error "Install Gunicorn: pip install fastapi-launcher[gunicorn]" SHALL be displayed

#### Scenario: Gunicorn on Windows
- **WHEN** user runs `fa start --server gunicorn` on Windows
- **THEN** error "Gunicorn is not supported on Windows" SHALL be displayed

### Requirement: Graceful Shutdown Timeout Option

The system SHALL support `--timeout-graceful-shutdown` option.

#### Scenario: Set graceful shutdown timeout
- **WHEN** user runs `fa start --timeout-graceful-shutdown 30`
- **THEN** server SHALL wait up to 30 seconds for requests to complete before shutdown

#### Scenario: Default timeout
- **WHEN** timeout-graceful-shutdown is not specified
- **THEN** default timeout of 10 seconds SHALL be used

## MODIFIED Requirements

### Requirement: Status Command

The system SHALL provide `fa status` command to show server status.

#### Scenario: Show running status
- **WHEN** user runs `fa status`
- **AND** server is running
- **THEN** Rich table SHALL display PID, port, memory, uptime

#### Scenario: Show not running
- **WHEN** user runs `fa status`
- **AND** server is not running
- **THEN** message "Server is not running" SHALL be displayed

#### Scenario: Verbose status with workers
- **WHEN** user runs `fa status --verbose`
- **AND** server is running with multiple workers
- **THEN** Rich table SHALL display each worker's PID, CPU%, memory, status
