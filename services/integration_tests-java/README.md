# Integration Tests

This directory contains basic integration tests for the scalable agent framework that test Kafka message flow and simulated service behavior.

## Overview

The integration tests currently provide basic testing of:
1. **Kafka message flow** between different topics
2. **Simulated service processing** using custom listeners
3. **Multi-tenant message routing** using proper tenant IDs (cyberdyne-systems, evil-corp)
4. **Basic error handling** and message validation

## Current Limitations

⚠️ **Important**: These tests are NOT comprehensive integration tests. They have significant limitations:

- **No actual service testing**: The tests don't start real DataPlane or ControlPlane Spring Boot applications
- **Simulated behavior only**: Service logic is simulated with custom Kafka listeners
- **No database persistence testing**: Real database operations are not tested
- **No actual business logic**: Real service business rules are not validated
- **Limited scope**: Only basic message flow and routing is tested

## Test Structure

### Configuration
- **`IntegrationTestConfig`**: Basic Kafka configuration for test environment
- **`BaseIntegrationTest`**: Common test utilities and Kafka setup
- **`SharedPostgreSQLContainer`**: PostgreSQL container for database testing (currently unused)

### Test Classes
- **`DataPlaneIntegrationTest`**: Tests simulated DataPlane message processing
- **`DataPlaneToControlPlaneIntegrationTest`**: Tests simulated service-to-service communication

## What the Tests Actually Do

1. **Create test messages** using `TestDataFactory`
2. **Send messages to Kafka topics** using `KafkaTemplate`
3. **Simulate service processing** with custom listeners
4. **Verify message flow** between topics
5. **Test multi-tenant isolation** using proper tenant IDs

## Future Improvements Needed

To make these truly comprehensive integration tests, the following would need to be implemented:

1. **Start actual Spring Boot services** (DataPlane, ControlPlane)
2. **Test real database persistence** using actual repositories
3. **Validate actual business logic** (guardrails, routing rules)
4. **Test real service-to-service communication**
5. **Add comprehensive error scenarios**
6. **Test actual multi-tenant data isolation**

## Running the Tests

```bash
mvn test -Dtest="*IntegrationTest"
```

## Test Data

The tests use proper tenant IDs as specified:
- `cyberdyne-systems`
- `evil-corp`

## Current Status

✅ **Working**: Basic Kafka message flow testing  
⚠️ **Limited**: Service simulation only  
❌ **Missing**: Real service integration testing 