## ADDED Requirements

### Requirement: CLI Entry Points

The system SHALL register two CLI entry points: `fa` and `fastapi-launcher`.

#### Scenario: Short command usage
- **WHEN** user runs `fa dev`
- **THEN** the development server SHALL start

#### Scenario: Full command usage
- **WHEN** user runs `fastapi-launcher dev`
- **THEN** the development server SHALL start (same as `fa dev`)

### Requirement: Development Mode Command

The system SHALL provide `fa dev` command for development mode with hot reload.

#### Scenario: Start dev server
- **WHEN** user runs `fa dev`
- **THEN** uvicorn SHALL start with reload=true and workers=1
- **AND** Rich panel SHALL display startup information

#### Scenario: Dev with custom port
- **WHEN** user runs `fa dev --port 3000`
- **THEN** server SHALL listen on port 3000

### Requirement: Production Mode Command

The system SHALL provide `fa start` command for production mode.

#### Scenario: Start production server
- **WHEN** user runs `fa start`
- **THEN** uvicorn SHALL start with reload=false

#### Scenario: Start with workers
- **WHEN** user runs `fa start --workers 4`
- **THEN** uvicorn SHALL spawn 4 worker processes

#### Scenario: Start as daemon
- **WHEN** user runs `fa start --daemon` on Unix
- **THEN** server SHALL run in background
- **AND** PID file SHALL be created

### Requirement: Stop Command

The system SHALL provide `fa stop` command to stop running server.

#### Scenario: Graceful stop
- **WHEN** user runs `fa stop`
- **AND** server is running
- **THEN** SIGTERM SHALL be sent to process
- **AND** process SHALL exit gracefully

#### Scenario: Force stop
- **WHEN** user runs `fa stop --force`
- **THEN** SIGKILL SHALL be sent to process

#### Scenario: No server running
- **WHEN** user runs `fa stop`
- **AND** no server is running
- **THEN** message "No server is running" SHALL be displayed

### Requirement: Restart Command

The system SHALL provide `fa restart` command to restart the server.

#### Scenario: Restart server
- **WHEN** user runs `fa restart`
- **AND** server is running
- **THEN** server SHALL be stopped and started again

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

### Requirement: Logs Command

The system SHALL provide `fa logs` command to view logs.

#### Scenario: View recent logs
- **WHEN** user runs `fa logs`
- **THEN** last 50 lines of fa.log SHALL be displayed

#### Scenario: Follow logs
- **WHEN** user runs `fa logs --follow`
- **THEN** logs SHALL be streamed in real-time

#### Scenario: View access logs
- **WHEN** user runs `fa logs --type access`
- **THEN** access.log content SHALL be displayed

### Requirement: Health Command

The system SHALL provide `fa health` command for health check.

#### Scenario: Health check success
- **WHEN** user runs `fa health`
- **AND** /health endpoint returns 200
- **THEN** "Healthy" status and response time SHALL be displayed

#### Scenario: Health check failure
- **WHEN** user runs `fa health`
- **AND** server is not responding
- **THEN** "Unhealthy" status and error SHALL be displayed

### Requirement: Config Command

The system SHALL provide `fa config` command to show effective configuration.

#### Scenario: Show config
- **WHEN** user runs `fa config`
- **THEN** Rich table SHALL display all merged configuration values

### Requirement: Check Command

The system SHALL provide `fa check` command to validate configuration and dependencies.

#### Scenario: All checks pass
- **WHEN** user runs `fa check`
- **AND** configuration is valid
- **AND** app path is valid
- **AND** FastAPI is installed
- **THEN** all check items SHALL show green checkmarks

#### Scenario: Missing dependency
- **WHEN** user runs `fa check`
- **AND** FastAPI is not installed
- **THEN** error SHALL indicate "FastAPI not found"

### Requirement: Clean Command

The system SHALL provide `fa clean` command to clean runtime files.

#### Scenario: Clean runtime
- **WHEN** user runs `fa clean`
- **THEN** runtime directory (PID file, logs) SHALL be deleted
- **AND** confirmation message SHALL be displayed

### Requirement: Version Display

The system SHALL support `fa --version` to display version.

#### Scenario: Show version
- **WHEN** user runs `fa --version`
- **THEN** version number SHALL be displayed

### Requirement: Shell Completion

The system SHALL support shell completion installation.

#### Scenario: Install completion
- **WHEN** user runs `fa --install-completion`
- **THEN** completion script SHALL be installed for user's shell

### Requirement: Uvicorn Passthrough

The system SHALL support passing arbitrary uvicorn arguments via `--`.

#### Scenario: Passthrough arguments
- **WHEN** user runs `fa dev -- --log-level debug`
- **THEN** uvicorn SHALL receive --log-level debug argument

### Requirement: First Run Guidance

The system SHALL display helpful guidance when configuration is missing.

#### Scenario: No config detected
- **WHEN** user runs `fa dev`
- **AND** no app is configured
- **AND** auto-discovery fails
- **THEN** system SHALL display quick start guide with example configuration

#### Scenario: Guide content
- **WHEN** quick start guide is displayed
- **THEN** it SHALL include:
  - Example pyproject.toml configuration
  - Common app path examples
  - Link to documentation
