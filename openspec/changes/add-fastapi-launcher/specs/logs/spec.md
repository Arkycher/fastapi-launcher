## ADDED Requirements

### Requirement: Log Directory Structure

The system SHALL organize logs in a structured directory.

#### Scenario: Default log structure
- **WHEN** server starts
- **THEN** logs SHALL be stored in:
  - runtime/logs/fa.log (application log)
  - runtime/logs/access.log (request log)
  - runtime/logs/error.log (error log)

#### Scenario: Custom log directory
- **WHEN** logging.dir = "logs/" is configured
- **THEN** all log files SHALL be stored in logs/ directory

### Requirement: Log Formats

The system SHALL support multiple log formats.

#### Scenario: Pretty format
- **WHEN** logging.format = "pretty" is configured
- **THEN** logs SHALL be formatted with colors and readable layout
- **AND** format SHALL be: "{time} | {level} | {message}"

#### Scenario: JSON format
- **WHEN** logging.format = "json" is configured
- **THEN** logs SHALL be JSON lines
- **AND** each line SHALL include: time, level, message, extra fields

### Requirement: Log Level Colors

The system SHALL colorize log output based on level (in pretty format).

#### Scenario: Level coloring
- **WHEN** pretty format is used
- **THEN** DEBUG SHALL be gray
- **AND** INFO SHALL be green
- **AND** WARNING SHALL be yellow
- **AND** ERROR SHALL be red

### Requirement: Access Log

The system SHALL record HTTP request logs.

#### Scenario: Access log entry
- **WHEN** HTTP request is processed
- **THEN** access log SHALL record:
  - Timestamp
  - HTTP method
  - Request path
  - Status code
  - Response time (ms)
  - Request ID (if available)

#### Scenario: Access log pretty format
- **WHEN** pretty format is used
- **THEN** format SHALL be: "{time} | {method} {path} | {status} | {duration}ms"

#### Scenario: Method coloring
- **WHEN** pretty format is used
- **THEN** GET SHALL be green
- **AND** POST SHALL be blue
- **AND** PUT SHALL be yellow
- **AND** DELETE SHALL be red

### Requirement: Slow Request Marking

The system SHALL mark slow requests in access log.

#### Scenario: Slow request detection
- **WHEN** request duration exceeds slow_threshold_ms (default: 1000ms)
- **THEN** log entry SHALL be marked with warning indicator
- **AND** in pretty format, entry SHALL be highlighted

### Requirement: Path Exclusion

The system SHALL support excluding paths from access log.

#### Scenario: Exclude health endpoint
- **WHEN** exclude_paths = ["/health", "/metrics"] is configured
- **AND** request to /health is received
- **THEN** request SHALL NOT be logged to access.log

### Requirement: Log Viewing

The system SHALL provide commands to view logs.

#### Scenario: View recent logs
- **WHEN** fa logs is executed
- **THEN** last N lines (default 50) SHALL be displayed
- **AND** output SHALL use Rich formatting

#### Scenario: Follow logs
- **WHEN** fa logs --follow is executed
- **THEN** logs SHALL stream in real-time
- **AND** user can Ctrl+C to stop

#### Scenario: View specific log type
- **WHEN** fa logs --type access is executed
- **THEN** only access.log content SHALL be displayed

#### Scenario: Custom line count
- **WHEN** fa logs --lines 100 is executed
- **THEN** last 100 lines SHALL be displayed

### Requirement: Log Directory Auto-Creation

The system SHALL automatically create log directories.

#### Scenario: Create log directory
- **WHEN** server starts
- **AND** log directory does not exist
- **THEN** log directory SHALL be created automatically

### Requirement: Log Level Configuration

The system SHALL support configurable log level.

#### Scenario: Default log level
- **WHEN** logging.level is not configured
- **THEN** default log level SHALL be INFO

#### Scenario: Custom log level
- **WHEN** logging.level = "DEBUG" is configured
- **THEN** DEBUG and above messages SHALL be logged

#### Scenario: Log level via environment
- **WHEN** FA_LOG_LEVEL=WARNING is set
- **THEN** WARNING and above messages SHALL be logged
