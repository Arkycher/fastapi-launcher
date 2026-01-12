## ADDED Requirements

### Requirement: Health Check Request

The system SHALL perform HTTP health check against configured endpoint.

#### Scenario: Successful health check
- **WHEN** fa health is executed
- **AND** server is running
- **AND** health endpoint returns 2xx status
- **THEN** output SHALL show "Healthy" with green indicator
- **AND** response time SHALL be displayed

#### Scenario: Failed health check
- **WHEN** fa health is executed
- **AND** health endpoint returns non-2xx status
- **THEN** output SHALL show "Unhealthy" with red indicator
- **AND** status code SHALL be displayed

#### Scenario: Connection refused
- **WHEN** fa health is executed
- **AND** server is not running
- **THEN** output SHALL show "Unreachable" with red indicator
- **AND** error message SHALL be displayed

### Requirement: Custom Health Endpoint

The system SHALL support configurable health endpoint.

#### Scenario: Default endpoint
- **WHEN** health_endpoint is not configured
- **THEN** health check SHALL target /health

#### Scenario: Custom endpoint
- **WHEN** health_endpoint = "/api/healthz" is configured
- **THEN** health check SHALL target /api/healthz

#### Scenario: CLI override
- **WHEN** fa health --endpoint /ping is executed
- **THEN** health check SHALL target /ping

### Requirement: Health Check Timeout

The system SHALL timeout health check requests.

#### Scenario: Timeout handling
- **WHEN** health endpoint does not respond within 10 seconds
- **THEN** output SHALL show "Timeout" with red indicator

### Requirement: Health Check Output

The system SHALL display health check results in Rich format.

#### Scenario: Rich output
- **WHEN** fa health is executed
- **THEN** output SHALL include:
  - Status indicator (icon + color)
  - Endpoint URL
  - Response time
  - Status code (if applicable)
  - Timestamp
