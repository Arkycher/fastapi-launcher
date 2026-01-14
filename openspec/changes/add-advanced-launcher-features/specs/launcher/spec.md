## ADDED Requirements

### Requirement: Gunicorn Backend Support

The system SHALL support Gunicorn as an alternative server backend.

#### Scenario: Start with Gunicorn
- **WHEN** user runs `fa start --server gunicorn`
- **THEN** Gunicorn SHALL be started with UvicornWorker
- **AND** worker count SHALL match --workers option

#### Scenario: Gunicorn worker management
- **WHEN** Gunicorn is running
- **AND** a worker process crashes
- **THEN** Gunicorn master SHALL automatically restart the worker

#### Scenario: Gunicorn max requests
- **WHEN** max_requests = 1000 is configured
- **THEN** each Gunicorn worker SHALL restart after 1000 requests to prevent memory leaks

#### Scenario: Gunicorn graceful reload
- **WHEN** SIGHUP is sent to Gunicorn master
- **THEN** workers SHALL be gracefully restarted one by one

### Requirement: Smart Mode Detection

The system SHALL automatically detect appropriate run mode.

#### Scenario: Detect via FA_ENV
- **WHEN** FA_ENV=production is set
- **THEN** production mode SHALL be selected

#### Scenario: Detect via PYTHON_ENV
- **WHEN** PYTHON_ENV=development is set
- **AND** FA_ENV is not set
- **THEN** development mode SHALL be selected

#### Scenario: Detect via NODE_ENV
- **WHEN** NODE_ENV=production is set
- **AND** FA_ENV and PYTHON_ENV are not set
- **THEN** production mode SHALL be selected

#### Scenario: Heuristic detection - development
- **WHEN** no environment variables are set
- **AND** .git directory exists
- **AND** .git/hooks/pre-commit exists
- **THEN** development mode SHALL be assumed

#### Scenario: Heuristic detection - production
- **WHEN** no environment variables are set
- **AND** Dockerfile or docker-compose.yml exists
- **THEN** production mode SHALL be assumed

#### Scenario: Default fallback
- **WHEN** no indicators are found
- **THEN** development mode SHALL be used as default

### Requirement: Graceful Shutdown

The system SHALL implement graceful shutdown with configurable timeout.

#### Scenario: Graceful shutdown on SIGTERM
- **WHEN** SIGTERM is received
- **AND** timeout_graceful_shutdown = 30
- **THEN** server SHALL:
  1. Stop accepting new connections
  2. Wait up to 30 seconds for active requests to complete
  3. Force terminate remaining connections after timeout

#### Scenario: Immediate shutdown on timeout exceeded
- **WHEN** graceful shutdown timeout is exceeded
- **THEN** remaining connections SHALL be forcefully closed
- **AND** exit code SHALL be 0 (clean exit)

### Requirement: Hot Reload Trigger

The system SHALL support manual hot reload triggering.

#### Scenario: SIGHUP triggers reload
- **WHEN** SIGHUP is sent to server process
- **AND** server is in development mode with reload enabled
- **THEN** server SHALL reload application code

#### Scenario: SIGHUP in production mode
- **WHEN** SIGHUP is sent to Gunicorn master
- **THEN** workers SHALL be gracefully restarted

## MODIFIED Requirements

### Requirement: Uvicorn Integration

The system SHALL use uvicorn as the default ASGI server, with Gunicorn as an optional alternative.

#### Scenario: Start uvicorn with config
- **WHEN** fa dev or fa start is executed
- **AND** --server is not specified or is "uvicorn"
- **THEN** uvicorn SHALL be started with merged configuration
- **AND** configuration SHALL include: host, port, workers, reload, log_level

#### Scenario: Start gunicorn with uvicorn workers
- **WHEN** fa start --server gunicorn is executed
- **THEN** gunicorn SHALL be started with UvicornWorker class
- **AND** configuration SHALL include: host, port, workers, timeout
