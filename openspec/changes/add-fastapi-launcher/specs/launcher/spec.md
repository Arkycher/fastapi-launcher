## ADDED Requirements

### Requirement: Uvicorn Integration

The system SHALL use uvicorn as the ASGI server.

#### Scenario: Start uvicorn with config
- **WHEN** fa dev or fa start is executed
- **THEN** uvicorn SHALL be started with merged configuration
- **AND** configuration SHALL include: host, port, workers, reload, log_level

### Requirement: Development Mode

The system SHALL provide development mode with hot reload.

#### Scenario: Dev mode settings
- **WHEN** fa dev is executed
- **THEN** uvicorn SHALL start with:
  - reload = true
  - workers = 1
  - log_level = debug (unless overridden)

#### Scenario: Dev mode with custom app
- **WHEN** fa dev --app "myapp.main:app" is executed
- **THEN** uvicorn SHALL load myapp.main:app

### Requirement: Production Mode

The system SHALL provide production mode with multiple workers.

#### Scenario: Prod mode settings
- **WHEN** fa start is executed
- **THEN** uvicorn SHALL start with:
  - reload = false
  - workers = configured value (default: CPU count)

#### Scenario: Prod with custom workers
- **WHEN** fa start --workers 8 is executed
- **THEN** uvicorn SHALL spawn 8 worker processes

### Requirement: App Auto-Discovery

The system SHALL attempt to discover FastAPI app if not configured.

#### Scenario: Auto-discover app
- **WHEN** app is not configured
- **THEN** system SHALL try these paths in order:
  1. main:app
  2. app.main:app
  3. src.main:app
  4. app:app

#### Scenario: App not found
- **WHEN** app is not configured
- **AND** none of the default paths exist
- **THEN** error SHALL display attempted paths and suggest configuration

#### Scenario: Multiple apps found
- **WHEN** multiple app paths are valid
- **THEN** first valid path SHALL be used
- **AND** info message SHALL indicate which path was selected

### Requirement: Startup Validation

The system SHALL validate configuration before starting uvicorn.

#### Scenario: Validate app path
- **WHEN** server starts
- **THEN** system SHALL verify app module can be imported
- **AND** app attribute exists in module

#### Scenario: Invalid app module
- **WHEN** app module cannot be imported
- **THEN** error SHALL display import error message

#### Scenario: Invalid app attribute
- **WHEN** module exists but attribute not found
- **THEN** error SHALL display "Attribute '{attr}' not found in module '{module}'"

### Requirement: Uvicorn Extra Parameters

The system SHALL support extra uvicorn parameters from config and CLI.

#### Scenario: Config uvicorn section
- **WHEN** [tool.fastapi-launcher.uvicorn] section exists
- **THEN** all keys SHALL be passed to uvicorn

#### Scenario: CLI passthrough
- **WHEN** user runs `fa dev -- --ssl-keyfile key.pem --ssl-certfile cert.pem`
- **THEN** SSL configuration SHALL be passed to uvicorn
