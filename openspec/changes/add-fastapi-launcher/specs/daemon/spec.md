## ADDED Requirements

### Requirement: Unix Daemon Mode

The system SHALL support running as a daemon on Unix systems.

#### Scenario: Start as daemon
- **WHEN** fa start --daemon is executed on Linux/macOS
- **THEN** process SHALL detach from terminal
- **AND** process SHALL run in background
- **AND** PID file SHALL be created

#### Scenario: Daemon double fork
- **WHEN** daemon mode starts
- **THEN** process SHALL perform double fork
- **AND** new session SHALL be created via setsid
- **AND** working directory SHALL remain unchanged

### Requirement: Stream Redirection

The system SHALL redirect standard streams when running as daemon.

#### Scenario: Stdout redirect
- **WHEN** daemon mode is active
- **THEN** stdout SHALL be redirected to log file

#### Scenario: Stderr redirect
- **WHEN** daemon mode is active
- **THEN** stderr SHALL be redirected to error log file

#### Scenario: Stdin close
- **WHEN** daemon mode is active
- **THEN** stdin SHALL be closed (redirected from /dev/null)

### Requirement: Windows Compatibility

The system SHALL handle daemon mode gracefully on Windows.

#### Scenario: Daemon on Windows
- **WHEN** fa start --daemon is executed on Windows
- **THEN** warning SHALL display: "Daemon mode is not supported on Windows"
- **AND** suggestion SHALL display: "Use nssm or Task Scheduler for background services"
- **AND** server SHALL NOT start in daemon mode

### Requirement: Log File Configuration

The system SHALL use configured log paths for daemon output.

#### Scenario: Default log paths
- **WHEN** daemon starts
- **AND** no log paths configured
- **THEN** stdout SHALL go to runtime/logs/fa.log
- **AND** stderr SHALL go to runtime/logs/error.log

#### Scenario: Custom log paths
- **WHEN** log_file = "logs/app.log" is configured
- **THEN** stdout/stderr SHALL go to configured path
