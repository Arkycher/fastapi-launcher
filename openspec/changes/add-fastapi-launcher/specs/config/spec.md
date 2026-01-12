## ADDED Requirements

### Requirement: Configuration Priority

The system SHALL merge configuration from multiple sources with the following priority (highest to lowest):
1. CLI arguments
2. Environment variables (FA_ prefix)
3. .env file (project root)
4. pyproject.toml [tool.fastapi-launcher] section
5. Default values

#### Scenario: CLI overrides all
- **WHEN** user provides --port 9000 via CLI
- **AND** FA_PORT=8080 is set in environment
- **AND** port = 8000 is set in pyproject.toml
- **THEN** the effective port SHALL be 9000

#### Scenario: Environment overrides file config
- **WHEN** FA_HOST=localhost is set in environment
- **AND** host = "0.0.0.0" is set in pyproject.toml
- **THEN** the effective host SHALL be localhost

### Requirement: Environment-Specific Configuration

The system SHALL support environment-specific configuration sections in pyproject.toml.

#### Scenario: Development environment config
- **WHEN** user runs `fa dev` or `fa start --env dev`
- **AND** [tool.fastapi-launcher.env.dev] section exists
- **THEN** values from dev section SHALL override base config

#### Scenario: Production environment config
- **WHEN** user runs `fa start --env prod`
- **AND** [tool.fastapi-launcher.env.prod] section exists
- **THEN** values from prod section SHALL override base config

### Requirement: .env File Support

The system SHALL automatically load environment variables from .env file in the project root.

#### Scenario: .env file loading
- **WHEN** .env file exists in project root
- **AND** contains FA_PORT=8888
- **THEN** the system SHALL use 8888 as port (unless overridden by ENV or CLI)

#### Scenario: Custom .env path
- **WHEN** env_file = "config/.env" is set in pyproject.toml
- **THEN** the system SHALL load from config/.env instead

### Requirement: Configuration Validation

The system SHALL validate configuration using Pydantic models and provide clear error messages.

#### Scenario: Invalid port number
- **WHEN** user provides --port 99999
- **THEN** the system SHALL display error: "Port must be between 1 and 65535"

#### Scenario: Invalid app path format
- **WHEN** app = "invalid" is configured (missing :)
- **THEN** the system SHALL display error: "App path must be in format 'module:attribute'"
