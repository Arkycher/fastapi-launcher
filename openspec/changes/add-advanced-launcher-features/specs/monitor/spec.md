## ADDED Requirements

### Requirement: Real-time Monitoring TUI

The system SHALL provide a TUI interface for real-time server monitoring.

#### Scenario: Start monitor
- **WHEN** user runs `fa monitor`
- **AND** server is running
- **THEN** Textual-based TUI SHALL display:
  - Server status (running/stopped)
  - Total CPU usage
  - Total memory usage
  - Requests per second (if available)
  - Uptime

#### Scenario: Monitor with multiple workers
- **WHEN** server is running with multiple workers
- **THEN** TUI SHALL display worker list table with:
  - Worker PID
  - Worker CPU%
  - Worker Memory (MB)
  - Worker Status
  - Requests Handled (Gunicorn only)

#### Scenario: Real-time refresh
- **WHEN** monitor is running
- **THEN** stats SHALL refresh every 1 second by default

#### Scenario: Custom refresh interval
- **WHEN** user runs `fa monitor --interval 5`
- **THEN** stats SHALL refresh every 5 seconds

### Requirement: Monitor Fallback Mode

The system SHALL provide non-TUI fallback for monitoring.

#### Scenario: No TUI mode
- **WHEN** user runs `fa monitor --no-tui`
- **THEN** simple CLI table SHALL be printed and refreshed in place

#### Scenario: Textual not installed
- **WHEN** user runs `fa monitor`
- **AND** textual is not installed
- **THEN** message SHALL suggest installing with `pip install fastapi-launcher[monitor]`
- **AND** offer to use --no-tui fallback

### Requirement: Monitor Keyboard Controls

The system SHALL support keyboard interaction in monitor TUI.

#### Scenario: Quit monitor
- **WHEN** user presses 'q' or Ctrl+C
- **THEN** monitor SHALL exit cleanly

#### Scenario: Refresh immediately
- **WHEN** user presses 'r'
- **THEN** stats SHALL refresh immediately

#### Scenario: Toggle worker details
- **WHEN** user presses 'w'
- **THEN** worker detail panel SHALL toggle visibility

### Requirement: Monitor Server Connection

The system SHALL detect server status in monitor.

#### Scenario: Server not running
- **WHEN** user runs `fa monitor`
- **AND** server is not running
- **THEN** message "Server is not running. Waiting for server to start..." SHALL be displayed
- **AND** monitor SHALL poll for server start every 2 seconds

#### Scenario: Server stops while monitoring
- **WHEN** monitor is running
- **AND** server stops
- **THEN** status SHALL change to "Stopped"
- **AND** message "Server stopped. Waiting for restart..." SHALL be displayed

### Requirement: Monitor Log Integration

The system SHALL optionally show recent logs in monitor.

#### Scenario: Show logs panel
- **WHEN** user runs `fa monitor --logs`
- **THEN** bottom panel SHALL show last 10 log entries
- **AND** new log entries SHALL appear in real-time

#### Scenario: Filter log level
- **WHEN** user runs `fa monitor --logs --log-level error`
- **THEN** only error level logs SHALL be displayed
