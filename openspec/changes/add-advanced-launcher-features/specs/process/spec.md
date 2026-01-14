## ADDED Requirements

### Requirement: Worker Status Tracking

The system SHALL track and report individual worker process status.

#### Scenario: Get Uvicorn worker status
- **WHEN** Uvicorn is running with workers > 1
- **THEN** system SHALL report for each worker:
  - PID
  - CPU percentage
  - Memory usage (MB)
  - Status (running/idle)
  - Uptime

#### Scenario: Get Gunicorn worker status
- **WHEN** Gunicorn is running
- **THEN** system SHALL report for each worker:
  - PID
  - CPU percentage
  - Memory usage (MB)
  - Requests handled (if available)
  - Status (running/idle/starting)
  - Uptime

#### Scenario: Worker process tree detection
- **WHEN** fa status --verbose is executed
- **THEN** system SHALL identify master process and all child worker processes

### Requirement: SIGHUP Signal Handling

The system SHALL handle SIGHUP signal for hot reload.

#### Scenario: Send SIGHUP to server
- **WHEN** fa reload is executed
- **AND** server is running
- **THEN** SIGHUP SHALL be sent to main server process

#### Scenario: SIGHUP propagation to workers
- **WHEN** SIGHUP is received by main process
- **THEN** signal SHALL be handled according to server backend:
  - Uvicorn: Trigger code reload
  - Gunicorn: Gracefully restart workers

## MODIFIED Requirements

### Requirement: Process Status Detection

The system SHALL detect and report process status including worker details.

#### Scenario: Get process info
- **WHEN** server is running
- **THEN** system SHALL report: PID, memory usage, CPU usage, start time, uptime

#### Scenario: Get detailed process info
- **WHEN** server is running with multiple workers
- **AND** verbose mode is requested
- **THEN** system SHALL report master process info AND each worker's info

#### Scenario: Process not found
- **WHEN** PID file exists but process is dead
- **THEN** system SHALL report process as not running

### Requirement: Signal Handling

The system SHALL handle Unix signals for graceful shutdown and reload.

#### Scenario: SIGTERM handling
- **WHEN** SIGTERM is received
- **THEN** server SHALL initiate graceful shutdown
- **AND** active requests SHALL complete before exit (within timeout)

#### Scenario: SIGINT handling
- **WHEN** SIGINT (Ctrl+C) is received
- **THEN** server SHALL initiate graceful shutdown

#### Scenario: SIGKILL sending
- **WHEN** fa stop --force is executed
- **THEN** SIGKILL SHALL be sent to forcefully terminate process

#### Scenario: SIGHUP handling
- **WHEN** SIGHUP is received
- **THEN** server SHALL trigger reload (dev mode) or worker restart (Gunicorn)
