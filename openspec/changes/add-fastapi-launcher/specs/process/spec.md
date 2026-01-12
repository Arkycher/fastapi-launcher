## ADDED Requirements

### Requirement: PID File Management

The system SHALL manage PID file for tracking running server process.

#### Scenario: Create PID file on start
- **WHEN** server starts successfully
- **THEN** PID file SHALL be created at configured path (default: runtime/fa.pid)
- **AND** file SHALL contain the main process PID

#### Scenario: Remove PID file on stop
- **WHEN** server stops (gracefully or forcefully)
- **THEN** PID file SHALL be deleted

#### Scenario: Stale PID file detection
- **WHEN** PID file exists
- **AND** process with that PID is not running
- **THEN** system SHALL treat server as not running
- **AND** stale PID file SHALL be cleaned up

### Requirement: Signal Handling

The system SHALL handle Unix signals for graceful shutdown.

#### Scenario: SIGTERM handling
- **WHEN** SIGTERM is received
- **THEN** server SHALL initiate graceful shutdown
- **AND** active requests SHALL complete before exit

#### Scenario: SIGINT handling
- **WHEN** SIGINT (Ctrl+C) is received
- **THEN** server SHALL initiate graceful shutdown

#### Scenario: SIGKILL sending
- **WHEN** fa stop --force is executed
- **THEN** SIGKILL SHALL be sent to forcefully terminate process

### Requirement: Process Status Detection

The system SHALL detect and report process status.

#### Scenario: Get process info
- **WHEN** server is running
- **THEN** system SHALL report: PID, memory usage, CPU usage, start time, uptime

#### Scenario: Process not found
- **WHEN** PID file exists but process is dead
- **THEN** system SHALL report process as not running

### Requirement: Port Conflict Detection

The system SHALL detect port conflicts before starting server.

#### Scenario: Port available
- **WHEN** configured port is not in use
- **THEN** server SHALL start normally

#### Scenario: Port in use
- **WHEN** configured port is already in use
- **THEN** error SHALL display: "Port {port} is already in use by process {pid} ({name})"

#### Scenario: Force port takeover
- **WHEN** port is in use
- **AND** user runs with --force flag
- **THEN** existing process SHALL be killed
- **AND** server SHALL start on that port

### Requirement: Runtime Directory Management

The system SHALL manage runtime directory for PID and log files.

#### Scenario: Auto-create runtime directory
- **WHEN** server starts
- **AND** runtime directory does not exist
- **THEN** runtime directory SHALL be created automatically

#### Scenario: Default runtime path
- **WHEN** runtime_dir is not configured
- **THEN** default path SHALL be "runtime/"
