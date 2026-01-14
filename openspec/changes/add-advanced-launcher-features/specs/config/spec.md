## ADDED Requirements

### Requirement: Multi-Environment Configuration

The system SHALL support named environment configurations in pyproject.toml.

#### Scenario: Define staging environment
- **WHEN** pyproject.toml contains:
  ```toml
  [tool.fastapi-launcher.envs.staging]
  host = "0.0.0.0"
  workers = 2
  log_level = "info"
  ```
- **AND** user runs `fa start --env staging`
- **THEN** these values SHALL override base configuration

#### Scenario: Environment inherits base config
- **WHEN** base config has port = 8000
- **AND** staging env does not specify port
- **THEN** staging SHALL use port = 8000 from base

#### Scenario: Multiple custom environments
- **WHEN** pyproject.toml contains envs.staging, envs.qa, envs.prod
- **THEN** each environment SHALL be independently selectable via --env

### Requirement: Graceful Shutdown Configuration

The system SHALL support graceful shutdown timeout configuration.

#### Scenario: Configure via pyproject.toml
- **WHEN** timeout_graceful_shutdown = 30 is set in config
- **THEN** server shutdown SHALL wait up to 30 seconds

#### Scenario: Configure via environment variable
- **WHEN** FA_TIMEOUT_GRACEFUL_SHUTDOWN=60 is set
- **THEN** shutdown timeout SHALL be 60 seconds

#### Scenario: CLI overrides config
- **WHEN** config has timeout_graceful_shutdown = 30
- **AND** user provides --timeout-graceful-shutdown 10
- **THEN** timeout SHALL be 10 seconds

### Requirement: Server Backend Configuration

The system SHALL support server backend configuration.

#### Scenario: Configure default backend
- **WHEN** server = "gunicorn" is set in config
- **THEN** Gunicorn SHALL be used by default for start command

#### Scenario: CLI overrides server backend
- **WHEN** config has server = "gunicorn"
- **AND** user provides --server uvicorn
- **THEN** Uvicorn SHALL be used

### Requirement: Gunicorn-Specific Configuration

The system SHALL support Gunicorn-specific settings when using Gunicorn backend.

#### Scenario: Max requests per worker
- **WHEN** max_requests = 1000 is configured
- **AND** server = "gunicorn"
- **THEN** each worker SHALL restart after handling 1000 requests

#### Scenario: Max requests jitter
- **WHEN** max_requests = 1000 and max_requests_jitter = 100 are configured
- **THEN** workers SHALL restart between 900-1100 requests (randomized)

#### Scenario: Worker class configuration
- **WHEN** worker_class = "uvicorn.workers.UvicornH11Worker" is configured
- **THEN** Gunicorn SHALL use specified worker class

## MODIFIED Requirements

### Requirement: Configuration Priority

The system SHALL merge configuration from multiple sources with the following priority (highest to lowest):
1. CLI arguments
2. Environment variables (FA_ prefix)
3. .env file (project root)
4. pyproject.toml [tool.fastapi-launcher.envs.<name>] section (if --env specified)
5. pyproject.toml [tool.fastapi-launcher] section
6. Default values

#### Scenario: CLI overrides all
- **WHEN** user provides --port 9000 via CLI
- **AND** FA_PORT=8080 is set in environment
- **AND** port = 8000 is set in pyproject.toml
- **THEN** the effective port SHALL be 9000

#### Scenario: Environment overrides file config
- **WHEN** FA_HOST=localhost is set in environment
- **AND** host = "0.0.0.0" is set in pyproject.toml
- **THEN** the effective host SHALL be localhost

#### Scenario: Named env overrides base config
- **WHEN** user runs `fa start --env staging`
- **AND** base config has workers = 1
- **AND** envs.staging has workers = 4
- **THEN** effective workers SHALL be 4
