# Architecture and Data Flow Documentation

## Overview

This document describes the scalable agent framework architecture with **4 core services** and **6 topic types** using Protocol Buffers for all message serialization to ensure type safety and performance benefits.

### Core Services Architecture

The system consists of **4 core microservices**:

1. **DataPlane** - Persists execution data and forwards protobuf messages to control topics
2. **ControlPlane** - Evaluates guardrails and routes full execution messages between PlanExecutors and TaskExecutors  
3. **TaskExecutor** - Executes individual tasks and publishes TaskExecution protobuf messages
4. **PlanExecutor** - Executes planning logic and publishes PlanExecution protobuf messages

### Topic Types and Naming Convention

The system uses **6 topic types** with tenant-aware naming following the pattern `{message-type}-{tenantId}`:

1. **task-executions-{tenantId}** - TaskExecutor publishes TaskExecution protobuf messages
2. **plan-executions-{tenantId}** - PlanExecutor publishes PlanExecution protobuf messages  
3. **persisted-task-executions-{tenantId}** - DataPlane forwards TaskExecution protobuf messages to ControlPlane
4. **persisted-plan-executions-{tenantId}** - DataPlane forwards PlanExecution protobuf messages to ControlPlane
5. **plan-inputs-{tenantId}** - ControlPlane publishes PlanInput protobuf messages for PlanExecutor
6. **task-inputs-{tenantId}** - ControlPlane publishes TaskInput protobuf messages for TaskExecutor

The topic naming pattern is implemented in `TopicNames.java` and `KafkaTopicPatterns.java` to ensure consistent tenant-aware routing across all services.

## Enhanced Parent-Child Relationship Tracking

The system now includes enhanced parent-child relationship tracking between TaskExecutions and PlanExecutions:

- **TaskExecution** tracks its parent PlanExecution via `parent_plan_exec_id` and `parent_plan_name` fields
- **PlanExecution** tracks its parent TaskExecutions via `parent_task_names` field (repeated string)
- **ExecutionHeader** now has `name` field (unique identifier of the Plan/Task that created this execution) and `exec_id` field (renamed from `id`)

## Enhanced Architecture Diagram

This diagram shows the high-level architecture of the microservices in the Scalable Agent Framework with all 6 topic types and tenant-aware naming.

```mermaid
graph TB

    %% Main Services
    subgraph "Core Microservices"
        ControlPlane(Control Plane)
        DataPlane(Data Plane)
        PlanExecutor(Plan Executor)
        TaskExecutor(Task Executor)

        Kafka[Apache Kafka<br/>Message Broker]
        PostgreSQL[(PostgreSQL<br/>Data Store)]
    end

    subgraph "Kafka Topics (6 types)"
        TE[task-executions-{tenantId}]
        PE[plan-executions-{tenantId}]
        PTE[persisted-task-executions-{tenantId}]
        PPE[persisted-plan-executions-{tenantId}]
        PI[plan-inputs-{tenantId}]
        TI[task-inputs-{tenantId}]
    end
    
    %% Service Connections with Topic Names
    PTE --> ControlPlane
    PPE --> ControlPlane
    ControlPlane --> PI
    ControlPlane --> TI

    PI --> PlanExecutor
    PlanExecutor --> PE

    TI --> TaskExecutor
    TaskExecutor --> TE

    PE --> DataPlane
    TE --> DataPlane
    DataPlane --> PTE
    DataPlane --> PPE

    DataPlane --> PostgreSQL
```

## Comprehensive Service Responsibilities

### DataPlane
- **Primary Role**: Persists execution data and forwards protobuf messages to control topics
- **Message Processing**: Consumes TaskExecution and PlanExecution protobuf messages from executors
- **Data Persistence**: Stores execution data to database using JPA entities with parent-child relationships
- **Message Forwarding**: Forwards protobuf messages to control topics without modification
- **State Management**: Maintains execution state and history across all tenants
- **Metadata Storage**: Stores task/plan definitions and configurations
- **Data Retrieval**: Provides APIs for querying execution data
- **Multi-tenancy**: Handles tenant-specific data isolation and routing

### ControlPlane
- **Primary Role**: Evaluates guardrails and routes full execution messages between PlanExecutors and TaskExecutors
- **Guardrail Evaluation**: Consumes TaskExecution and PlanExecution protobuf messages from data plane
- **Policy Enforcement**: Enforces policies and constraints on agent behavior
- **Graph Lookup**: Examines TaskExecution to determine next plan in graph path
- **Message Routing**: Publishes PlanInput and TaskInput protobuf messages to kafka topics
- **Request Validation**: Validates incoming requests against policies
- **Multi-tenancy**: Routes messages to appropriate tenant-specific topics
- **Execution Coordination**: Coordinates between planning and execution phases

### TaskExecutor
- **Primary Role**: Executes individual tasks and publishes TaskExecution protobuf messages
- **Task Execution**: Executes individual tasks based on registered implementations
- **Message Processing**: Consumes TaskInput protobuf messages from control plane
- **Result Processing**: Processes and forwards execution results
- **Registry Management**: Maintains registry of available tasks
- **Task Handlers**: Executes different types of tasks (text generation, code execution, data processing)
- **Parent Tracking**: Creates TaskExecution with parent plan information
- **Multi-tenancy**: Publishes to tenant-specific task execution topics

### PlanExecutor
- **Primary Role**: Executes planning logic and publishes PlanExecution protobuf messages
- **Plan Execution**: Orchestrates plan execution and task sequencing
- **Message Processing**: Consumes PlanInput protobuf messages from control plane
- **Result Processing**: Processes and forwards execution results
- **Registry Management**: Maintains registry of available plans
- **Plan Handlers**: Executes different types of plans (sequential, conditional, parallel)
- **Parent Tracking**: Creates PlanExecution with parent task information
- **Multi-tenancy**: Publishes to tenant-specific plan execution topics

## Tenant-Aware Configuration with KafkaTopicPatterns

The system implements comprehensive tenant-aware configuration using `KafkaTopicPatterns.java` and `TenantAwareKafkaConfig.java` to enable dynamic topic subscription and multi-tenant message routing.

### KafkaTopicPatterns Implementation

The `KafkaTopicPatterns.java` class uses Spring Boot's `@ConfigurationProperties` to load topic patterns from `application.yml`. See the actual implementation in `services/common-java/src/main/java/com/pcallahan/agentic/common/KafkaTopicPatterns.java`.

### Dynamic Topic Subscription

Services use regex patterns for dynamic topic subscription, enabling tenant-aware routing. See the actual implementation in the Kafka listener classes throughout the services.

### TenantAwareKafkaConfig Integration

The `TenantAwareKafkaConfig.java` class provides tenant-specific configuration with comprehensive error handling and isolation strategies.

**Tenant Isolation**: Each tenant's configuration is isolated to prevent cross-tenant interference.

**Error Handling**: Tenant-specific error handling ensures failures in one tenant don't affect others.

**Resource Management**: Per-tenant resource limits and monitoring prevent resource exhaustion.

**Configuration Validation**: Tenant configurations are validated to ensure proper setup.

**Configuration Strategy**: The system provides tenant-specific configuration with comprehensive error handling and isolation strategies. Each tenant's configuration is isolated to prevent cross-tenant interference, tenant-specific error handling ensures failures in one tenant don't affect others, per-tenant resource limits prevent resource exhaustion, and tenant configurations are validated to ensure proper setup.

### Configuration Examples

**application.yml Configuration**: See the actual configuration in the respective service `application.yml` files.

**Consumer Group Naming Strategy**:
- Each tenant gets its own consumer group: `consumer-group-{tenantId}`
- Prevents message consumption conflicts between tenants
- Enables independent scaling per tenant

### Tenant Validation and Active Tenant Tracking

The system validates tenant information and tracks active tenants with comprehensive error handling and monitoring.

**Tenant Validation**: Tenant IDs are validated for format and existence before processing.

**Active Tenant Tracking**: The system maintains a registry of active tenants for monitoring and resource management.

**Tenant Health Monitoring**: Each tenant's processing health is monitored independently.

**Error Isolation**: Tenant-specific errors are isolated to prevent cross-tenant impact.

**Validation Strategy**: The system validates tenant information and tracks active tenants with comprehensive error handling and monitoring. Tenant IDs are validated for format and existence before processing, the system maintains a registry of active tenants for monitoring and resource management, each tenant's processing health is monitored independently, and tenant-specific errors are isolated to prevent cross-tenant impact.

## Message Serialization Patterns using ProtobufUtils

The system uses `ProtobufUtils.java` for comprehensive serialization/deserialization of all protobuf message types with robust error handling and validation.

### Comprehensive Serialization Methods

`ProtobufUtils` provides complete serialization coverage for all message types. See the actual implementation in `services/common-java/src/main/java/com/pcallahan/agentic/common/ProtobufUtils.java`.

### Error Handling Patterns

The serialization utilities implement comprehensive error handling patterns:

**Validation Errors**: Invalid protobuf messages are detected early with detailed error messages.

**Serialization Failures**: Failed serialization is handled gracefully with proper exception handling.

**Deserialization Failures**: Corrupted or invalid data is handled with appropriate error recovery.

**Performance Monitoring**: Serialization performance is monitored to detect potential bottlenecks.

**Error Handling Strategy**: The system implements comprehensive error handling for serialization operations. Invalid protobuf messages are detected early with detailed error messages, failed serialization is handled gracefully with proper exception handling, corrupted data is handled with appropriate error recovery, and serialization performance is monitored to detect potential bottlenecks.

### Usage Examples in Services

**TaskExecutorService Usage**: The TaskExecutorService demonstrates serialization patterns for task execution messages with comprehensive error handling and validation.

**DataPlane Persistence Usage**: The DataPlane service shows persistence patterns for execution data with robust error handling and retry mechanisms.

**Service Usage Strategy**: Services demonstrate serialization patterns for different message types with comprehensive error handling and validation. The TaskExecutorService shows patterns for task execution messages, while the DataPlane service demonstrates persistence patterns for execution data with robust error handling and retry mechanisms.

### Binary Serialization Benefits

The protobuf implementation provides significant benefits:

1. **Type Safety**: Compile-time validation of message structures
2. **Performance**: Efficient binary serialization/deserialization
3. **Schema Evolution**: Backward/forward compatibility for message changes
4. **Consistency**: Uniform message format across all services
5. **Validation**: Built-in message validation and error handling

## Error Handling Strategies and Acknowledgment Patterns

The system implements comprehensive error handling strategies using manual acknowledgment patterns for reliable message processing and error recovery.

### Manual Acknowledgment Patterns

All Kafka listeners use manual acknowledgment for precise control over message processing. This pattern allows services to:

- **Selective Acknowledgment**: Only acknowledge messages after successful processing
- **Retry Control**: Failed messages remain in the queue for automatic retry
- **Error Isolation**: Prevent message loss during transient failures
- **Processing Guarantees**: Ensure exactly-once processing semantics

**Pattern**: Services only acknowledge messages after successful processing, allowing failed messages to remain in the queue for automatic retry. This ensures no message loss during transient failures and provides exactly-once processing semantics.

### Error Recovery Strategies

The system implements several error recovery strategies:

**Deserialization Failures**: Messages with invalid protobuf format are acknowledged to prevent infinite retry loops, while logging the error for investigation.

**Business Logic Failures**: Processing errors are logged but don't block message acknowledgment, allowing the system to continue processing other messages.

**Database Failures**: Persistence errors are logged but don't prevent message forwarding to downstream services, ensuring the execution flow continues.

**Network Failures**: Transient network issues trigger automatic retry through Kafka's built-in retry mechanisms.

### Tenant-Aware Error Handling

The system implements tenant-specific error handling to ensure:

- **Isolated Failures**: Errors in one tenant don't affect others
- **Tenant-Specific Logging**: Error logs include tenant context for debugging
- **Custom Error Policies**: Different tenants can have different error handling policies
- **Resource Isolation**: Failed processing in one tenant doesn't consume resources for others

**Strategy**: The system implements tenant-specific error handling that isolates failures between tenants, includes tenant context in error logs for debugging, and allows different error handling policies per tenant to ensure resource isolation.

### Graceful Degradation Patterns

The system implements graceful degradation for various failure scenarios:

**Service Unavailability**: When downstream services are unavailable, messages are queued and retried automatically.

**Resource Exhaustion**: When system resources are limited, processing is throttled rather than failing completely.

**Partial Failures**: When only part of a multi-step process fails, the system continues with available components.

**Configuration Errors**: Invalid configurations are logged and default values are used where possible.

### Consumer Configuration with Manual Acknowledgment

All services configure Kafka consumers with manual acknowledgment to enable:

- **Precise Control**: Exact control over when messages are acknowledged
- **Error Recovery**: Failed messages remain available for retry
- **Processing Guarantees**: Ensure messages are processed exactly once
- **Monitoring**: Track message processing success/failure rates

### Logging Strategies for Error Tracking

Comprehensive logging enables error tracking and debugging through:

**Structured Logging**: JSON-formatted logs with consistent fields for easy parsing and analysis.

**Error Context**: Each error log includes relevant context (tenant ID, message type, execution ID).

**Performance Metrics**: Track processing times and error rates for monitoring and alerting.

**Audit Trails**: Complete audit trails for compliance and debugging purposes.

**Logging Pattern**: The system uses structured logging with consistent fields including tenant ID, execution ID, error details, and retry counts for easy parsing, analysis, and debugging across all services.

## Hub-and-Spoke Architecture Pattern

The system implements a hub-and-spoke architecture pattern where DataPlane acts as the central hub, ControlPlane serves as the routing engine, and executor services (TaskExecutor, PlanExecutor) function as spokes.

### DataPlane as the Central Hub

DataPlane serves as the central hub that receives all execution messages from executor services. See the actual implementation in `services/data_plane-java/src/main/java/com/pcallahan/agentic/dataplane/service/PersistenceService.java`.

### ControlPlane as the Routing Engine

ControlPlane acts as the intelligent routing engine that directs messages between executors. See the actual implementation in `services/control_plane-java/src/main/java/com/pcallahan/agentic/controlplane/service/ExecutionRouter.java`.

### Spoke Services (Executors)

TaskExecutor and PlanExecutor function as spoke services that publish to and consume from the hub. See the actual implementations in:
- `services/task_executor-java/src/main/java/com/pcallahan/agentic/taskexecutor/service/TaskExecutorService.java`
- `services/plan_executor-java/src/main/java/com/pcallahan/agentic/planexecutor/service/PlanExecutorService.java`

### Message Flow Patterns

The hub-and-spoke pattern enables specific message flow patterns:

```mermaid
graph TB
    subgraph "Spoke Services"
        TE[TaskExecutor]
        PE[PlanExecutor]
    end
    
    subgraph "Central Hub"
        DP[DataPlane]
    end
    
    subgraph "Routing Engine"
        CP[ControlPlane]
    end
    
    subgraph "Kafka Topics"
        TE_T[task-executions-{tenantId}]
        PE_T[plan-executions-{tenantId}]
        PTE_T[persisted-task-executions-{tenantId}]
        PPE_T[persisted-plan-executions-{tenantId}]
        TI_T[task-inputs-{tenantId}]
        PI_T[plan-inputs-{tenantId}]
    end
    
    TE --> TE_T
    PE --> PE_T
    TE_T --> DP
    PE_T --> DP
    DP --> PTE_T
    DP --> PPE_T
    PTE_T --> CP
    PPE_T --> CP
    CP --> TI_T
    CP --> PI_T
    TI_T --> TE
    PI_T --> PE
```

### Benefits of Hub-and-Spoke Pattern

1. **Centralized Data Management**: All execution data flows through DataPlane hub
2. **Intelligent Routing**: ControlPlane provides centralized routing logic
3. **Scalability**: Spoke services can scale independently
4. **Decoupling**: Executors are decoupled from each other
5. **Tenant Isolation**: Each tenant's messages are isolated through topic patterns
6. **Service Independence**: Spoke services can be deployed and scaled independently

### Comparison with Point-to-Point Messaging

**Hub-and-Spoke Advantages**:
- Centralized control and monitoring
- Simplified routing logic
- Better error handling and recovery
- Easier to implement tenant isolation
- Reduced coupling between services

**Point-to-Point Disadvantages**:
- Complex routing between multiple services
- Difficult to implement tenant isolation
- Harder to monitor and debug
- Tight coupling between services

### Implementation in Kafka Topics

The hub-and-spoke pattern is implemented through specific topic usage:

1. **Hub Topics** (DataPlane receives from all executors):
   - `task-executions-{tenantId}` - All TaskExecutions from TaskExecutor
   - `plan-executions-{tenantId}` - All PlanExecutions from PlanExecutor

2. **Control Topics** (ControlPlane routes between executors):
   - `persisted-task-executions-{tenantId}` - DataPlane forwards to ControlPlane
   - `persisted-plan-executions-{tenantId}` - DataPlane forwards to ControlPlane
   - `task-inputs-{tenantId}` - ControlPlane routes to TaskExecutor
   - `plan-inputs-{tenantId}` - ControlPlane routes to PlanExecutor

This architecture ensures that all execution data flows through the central hub (DataPlane) while the routing engine (ControlPlane) intelligently directs messages between executor services based on execution results and graph navigation logic.

## Service-Specific Kafka Listeners and Producers

The system implements comprehensive Kafka infrastructure with service-specific listeners and producers, each configured with specific topic patterns, consumer groups, and tenant-aware routing.

### ControlPlane Service Kafka Infrastructure

**Listeners**:
- **Persisted Task Executions Listener**: Consumes from `persisted-task-executions-.*` pattern with consumer group `control-plane-persisted-task-executions`
- **Persisted Plan Executions Listener**: Consumes from `persisted-plan-executions-.*` pattern with consumer group `control-plane-persisted-plan-executions`

**Producers**:
- **Plan Inputs Producer**: Publishes to `plan-inputs-{tenantId}` topics using `TopicNames.planInputs(tenantId)` utility
- **Task Inputs Producer**: Publishes to `task-inputs-{tenantId}` topics using `TopicNames.taskInputs(tenantId)` utility

**Configuration**: See the actual configuration in `services/control_plane-java/src/main/resources/application.yml`.

### DataPlane Service Kafka Infrastructure

**Listeners**:
- **Task Executions Listener**: Consumes from `task-executions-.*` pattern with consumer group `data-plane-task-executions`
- **Plan Executions Listener**: Consumes from `plan-executions-.*` pattern with consumer group `data-plane-plan-executions`

**Producers**:
- **Persisted Task Executions Producer**: Publishes to `persisted-task-executions-{tenantId}` topics using `TopicNames.persistedTaskExecutions(tenantId)` utility
- **Persisted Plan Executions Producer**: Publishes to `persisted-plan-executions-{tenantId}` topics using `TopicNames.persistedPlanExecutions(tenantId)` utility

**Configuration**: See the actual configuration in `services/data_plane-java/src/main/resources/application.yml`.

### TaskExecutor Service Kafka Infrastructure

**Listeners**:
- **Task Inputs Listener**: Consumes from `task-inputs-.*` pattern with consumer group `task-executor-task-inputs`

**Producers**:
- **Task Executions Producer**: Publishes to `task-executions-{tenantId}` topics using `TopicNames.taskExecutions(tenantId)` utility

**Configuration**: See the actual configuration in `services/task_executor-java/src/main/resources/application.yml`.

### PlanExecutor Service Kafka Infrastructure

**Listeners**:
- **Plan Inputs Listener**: Consumes from `plan-inputs-.*` pattern with consumer group `plan-executor-plan-inputs`

**Producers**:
- **Plan Executions Producer**: Publishes to `plan-executions-{tenantId}` topics using `TopicNames.planExecutions(tenantId)` utility

**Configuration**: See the actual configuration in `services/plan_executor-java/src/main/resources/application.yml`.

### Topic Pattern Implementation

The `KafkaTopicPatterns.java` class provides centralized topic pattern configuration. See the actual implementation in `services/common-java/src/main/java/com/pcallahan/agentic/common/KafkaTopicPatterns.java`.

## Message Key Strategies and Partitioning Logic

The system implements sophisticated message key strategies and partitioning logic to ensure ordered processing and tenant-aware message distribution.

### Message Key Derivation from Protobuf Fields

Message keys are derived from protobuf message fields to enable intelligent partitioning:

**TaskExecution Message Keys**: Message keys are derived from `taskExecution.getHeader().getName()` (task_name from ExecutionHeader). See the actual implementation in the producer classes throughout the services.

**PlanExecution Message Keys**: Message keys are derived from `planExecution.getHeader().getName()` (plan_name from ExecutionHeader). See the actual implementation in the producer classes throughout the services.

**PlanInput Message Keys**: Message keys are derived from `planInput.getPlanName()` (plan_name from PlanInput). See the actual implementation in the producer classes throughout the services.

**TaskInput Message Keys**: Message keys are derived from `taskInput.getTaskName()` (task_name from TaskInput). See the actual implementation in the producer classes throughout the services.

### Partitioning Strategy Benefits

**Tenant-Aware Partitioning**:
- Messages for the same tenant and task/plan are co-located on the same partition
- Ensures ordered processing of related messages within a tenant
- Prevents message ordering issues across different tenants

**Ordered Processing Guarantees**:
- All messages with the same key (task/plan name) go to the same partition
- Maintains execution order for related tasks and plans
- Enables sequential processing of dependent operations

**Scalability Benefits**:
- Parallel processing across different partitions
- Independent scaling of partition consumers
- Load distribution across available partitions

### Implementation Examples

**TaskExecutorService Message Production**: See the actual implementation in `services/task_executor-java/src/main/java/com/pcallahan/agentic/taskexecutor/service/TaskExecutorService.java`.

**DataPlane Message Forwarding**: See the actual implementation in `services/data_plane-java/src/main/java/com/pcallahan/agentic/dataplane/service/PersistenceService.java`.

### Partition Assignment Strategy

The system uses consistent hashing for partition assignment:

Messages with the same key always go to the same partition, while different keys are distributed across available partitions. Tenant-specific topics ensure tenant isolation at the topic level.

## Consumer Group Configurations and Tenant Isolation

The system implements comprehensive consumer group configurations with tenant isolation strategies to ensure reliable message processing and multi-tenant support.

### Service-Specific Consumer Group Naming

Each service uses specific consumer group patterns from `application.yml` configurations:

**Consumer Groups**: Each service uses specific consumer group patterns from `application.yml` configurations. See the actual configurations in the respective service `application.yml` files.

### TenantAwareKafkaConfig Implementation

The `TenantAwareKafkaConfig.java` class provides tenant-aware consumer factory configuration. See the actual implementation in `services/common-java/src/main/java/com/pcallahan/agentic/common/TenantAwareKafkaConfig.java`.

### Manual Acknowledgment Configuration

All services use manual acknowledgment mode for precise error handling control. See the actual implementation in the Kafka configuration classes in each service.

### Tenant Isolation Strategies

**Consumer Group Isolation**:
- Each service has its own consumer group
- Prevents message consumption conflicts between services
- Enables independent scaling per service

**Topic Pattern Isolation**:
- Tenant-specific topic patterns: `{message-type}-{tenantId}`
- Regex patterns enable dynamic topic subscription
- Automatic tenant filtering through topic naming

**Error Handler Isolation**:
The system implements tenant-specific error handlers to ensure isolated error processing and recovery strategies per tenant.

**Error Handler Strategy**: The system implements tenant-specific error handlers to ensure isolated error processing and recovery strategies per tenant. Each tenant can have different error handling policies, errors in one tenant don't affect others, and the system provides tenant-specific error recovery mechanisms.

### Configuration Properties

**Configuration Properties**: The system uses comprehensive configuration properties for error handling, retry policies, and tenant isolation.

**Configuration Strategy**: The system uses comprehensive configuration properties for error handling, retry policies, and tenant isolation. Configuration includes consumer settings, retry policies with exponential backoff, error handling strategies with dead letter queues and circuit breakers, and tenant-specific configurations that allow different error handling policies per tenant.

### Concurrency and Parallelism

**Parallel Processing Configuration**: Services use concurrent consumers for increased throughput and better resource utilization with comprehensive error handling and monitoring.

**Concurrency Strategy**: Services use concurrent consumers for increased throughput and better resource utilization with comprehensive error handling and monitoring. The system configures multiple concurrent consumers per service, implements tenant-aware error handlers, and uses retry templates with exponential backoff policies to ensure reliable message processing.

**Benefits of Parallel Processing**:
- Multiple consumers within the same consumer group
- Increased throughput for message processing
- Better resource utilization
- Fault tolerance through consumer redundancy

## Complete Message Lifecycle from Production to Consumption

The system implements a comprehensive message lifecycle that traces messages from production through consumption with all intermediate steps, error handling, and monitoring.

### Step 1: Message Production by Executor Services

**TaskExecutor Message Production**: See the actual implementation in `services/task_executor-java/src/main/java/com/pcallahan/agentic/taskexecutor/service/TaskExecutorService.java`.

**PlanExecutor Message Production**: See the actual implementation in `services/plan_executor-java/src/main/java/com/pcallahan/agentic/planexecutor/service/PlanExecutorService.java`.

### Step 2: Topic Routing Using TopicNames Utility

**TopicNames Utility Implementation**: See the actual implementation in `services/common-java/src/main/java/com/pcallahan/agentic/common/TopicNames.java`.

### Step 3: Kafka Partitioning Based on Message Keys

**Partition Assignment Logic**: Kafka automatically assigns partitions based on message keys. Messages with the same key go to the same partition, while different keys are distributed across available partitions. Tenant-specific topics ensure tenant isolation.

**Partitioning Benefits**:
- Ordered processing of related messages
- Tenant isolation through topic separation
- Parallel processing across partitions
- Load distribution and scalability

### Step 4: Message Consumption by Target Services

**DataPlane Message Consumption**: See the actual implementation in `services/data_plane-java/src/main/java/com/pcallahan/agentic/dataplane/service/PersistenceService.java`.

### Step 5: Protobuf Deserialization Using ProtobufUtils

**Deserialization with Error Handling**: See the actual implementation in `services/common-java/src/main/java/com/pcallahan/agentic/common/ProtobufUtils.java`.

### Step 6: Tenant ID Extraction from Topic Names

**Tenant ID Extraction Logic**: See the actual implementation in `services/common-java/src/main/java/com/pcallahan/agentic/common/TopicNames.java`.

**Usage in Services**: See the actual implementation in the Kafka listener classes throughout the services.

### Step 7: Message Processing by Service-Specific Business Logic

**DataPlane Business Logic**: See the actual implementation in `services/data_plane-java/src/main/java/com/pcallahan/agentic/dataplane/service/PersistenceService.java`.

**ControlPlane Business Logic**: See the actual implementation in `services/control_plane-java/src/main/java/com/pcallahan/agentic/controlplane/service/ExecutionRouter.java`.

### Step 8: Manual Acknowledgment for Successful Processing

**Acknowledgment Patterns**: See the actual implementation in `services/task_executor-java/src/main/java/com/pcallahan/agentic/taskexecutor/service/TaskExecutorService.java`.

### Step 9: Downstream Message Production to Continue Execution Flow

**Message Forwarding Patterns**: See the actual implementation in `services/control_plane-java/src/main/java/com/pcallahan/agentic/controlplane/service/ExecutionRouter.java`.

### Error Handling and Retry Mechanisms

The system implements comprehensive error handling and retry mechanisms:

**Retry Policies**: Configurable retry policies with exponential backoff for transient failures.

**Dead Letter Queues**: Messages that fail repeatedly are moved to dead letter queues for manual investigation.

**Circuit Breakers**: Circuit breakers prevent cascading failures when downstream services are unavailable.

**Health Checks**: Regular health checks ensure services are available and functioning correctly.

**Retry Strategy**: The system implements configurable retry policies with exponential backoff for transient failures, dead letter queues for repeatedly failed messages, circuit breakers to prevent cascading failures, and health checks to ensure service availability.

### Monitoring and Logging Patterns

The system implements comprehensive monitoring and logging patterns:

**Message Lifecycle Tracking**: Each message is tracked through its complete lifecycle with unique correlation IDs.

**Performance Metrics**: Processing times, throughput, and error rates are monitored for each service.

**Health Monitoring**: Service health is continuously monitored with detailed status information.

**Alerting**: Automated alerts are triggered for critical failures and performance degradation.

**Monitoring Pattern**: The system tracks each message through its complete lifecycle with unique correlation IDs, monitors processing times and throughput, continuously checks service health, and triggers automated alerts for critical failures and performance degradation.

### Complete Lifecycle Example

The complete message lifecycle includes production, routing, consumption, processing, and acknowledgment phases with comprehensive error handling and monitoring.

**Lifecycle Phases**:
1. **Message Production**: Services create protobuf messages with proper validation
2. **Topic Routing**: Messages are routed to appropriate tenant-specific topics
3. **Message Consumption**: Target services consume messages with error handling
4. **Processing**: Business logic processes messages with retry mechanisms
5. **Acknowledgment**: Successful processing triggers message acknowledgment
6. **Monitoring**: Complete observability throughout the entire flow

**Lifecycle Strategy**: The complete message lifecycle includes validation, processing, persistence, acknowledgment, and monitoring phases. The system handles different error types appropriately - validation errors are acknowledged to prevent retry loops, while processing errors trigger retry mechanisms. Each phase includes comprehensive logging and error tracking.

This comprehensive message lifecycle ensures reliable message processing, proper error handling, and complete observability throughout the entire execution flow.

## Complete Execution Cycle

This comprehensive flow shows the complete execution cycle from initial trigger through all services, including routing logic and parent-child relationship tracking.

The complete execution cycle includes task execution, data plane processing, control plane routing, and plan execution phases with enhanced parent-child tracking. See the actual implementation in the service classes throughout the codebase.

## Detailed Task Execution Flow

### Step-by-Step Breakdown with Routing Logic

1. **Initial TaskInput Consumption**
   - TaskExecutor consumes TaskInput from `task-inputs-{tenantId}` topic
   - TaskInput contains original PlanExecution context and task metadata
   - Service extracts task name and PlanExecution from TaskInput

2. **Task Execution with Parent Tracking**
   - TaskExecutor creates TaskExecution with enhanced parent relationship fields:
     - `header.name` = task_name (unique identifier of the task)
     - `header.exec_id` = new UUID (unique execution identifier)
     - `parent_plan_exec_id` = plan.header.exec_id (links to parent PlanExecution)
     - `parent_plan_name` = plan.header.name (links to parent PlanExecution name)
   - Task execution logic processes the task using registered TaskHandler
   - TaskResult is created with execution output and metadata

3. **TaskExecution Publishing**
   - TaskExecution protobuf message is published to `task-executions-{tenantId}`
   - Message includes all parent-child relationship tracking fields
   - Kafka producer ensures reliable delivery to DataPlane

4. **DataPlane Persistence and Forwarding**
   - DataPlane consumes TaskExecution from `task-executions-{tenantId}`
   - Service persists execution data to PostgreSQL with parent tracking fields:
     - `parent_plan_exec_id` stored in TaskExecutionEntity
     - `parent_plan_name` stored in TaskExecutionEntity
   - TaskExecution is republished to `persisted-task-executions-{tenantId}` without modification

5. **ControlPlane Routing Logic**
   - ControlPlane consumes TaskExecution from `persisted-task-executions-{tenantId}`
   - GuardrailEngine evaluates TaskExecution against policies and constraints
   - If approved, ExecutionRouter examines TaskExecution to determine next steps:
     - Extracts `result.next_task_names` from TaskExecution
     - Looks up Task metadata using TaskLookupService
     - Creates TaskInput messages for each next task
   - TaskInput messages are published to `task-inputs-{tenantId}` with original TaskExecution context

### Parent-Child Relationship Field Mappings

| Field | Source | Target | Purpose |
|-------|--------|--------|---------|
| `parent_plan_exec_id` | PlanExecution.header.exec_id | TaskExecution.parent_plan_exec_id | Links TaskExecution to parent PlanExecution |
| `parent_plan_name` | PlanExecution.header.name | TaskExecution.parent_plan_name | Identifies parent PlanExecution by name |
| `header.name` | Task definition | TaskExecution.header.name | Unique identifier of the task that created this execution |
| `header.exec_id` | Generated UUID | TaskExecution.header.exec_id | Unique identifier for this specific execution |

## Detailed Plan Execution Flow

### Step-by-Step Breakdown with Routing Logic

1. **Initial PlanInput Consumption**
   - PlanExecutor consumes PlanInput from `plan-inputs-{tenantId}` topic
   - PlanInput contains TaskExecution objects that provide context for plan execution
   - Service extracts plan name and TaskExecution list from PlanInput

2. **Plan Execution with Parent Tracking**
   - PlanExecutor creates PlanExecution with enhanced parent relationship fields:
     - `header.name` = plan_name (unique identifier of the plan)
     - `header.exec_id` = new UUID (unique execution identifier)
     - `parent_task_names` = [task.header.name, ...] (list of parent TaskExecution names)
   - Plan execution logic processes the plan using registered PlanHandler
   - PlanResult is created with execution output and next task names

3. **PlanExecution Publishing**
   - PlanExecution protobuf message is published to `plan-executions-{tenantId}`
   - Message includes all parent-child relationship tracking fields
   - Kafka producer ensures reliable delivery to DataPlane

4. **DataPlane Persistence and Forwarding**
   - DataPlane consumes PlanExecution from `plan-executions-{tenantId}`
   - Service persists execution data to PostgreSQL with parent tracking fields:
     - `parent_task_names` stored as repeated string in PlanExecutionEntity
   - PlanExecution is republished to `persisted-plan-executions-{tenantId}` without modification

5. **ControlPlane Routing Logic**
   - ControlPlane consumes PlanExecution from `persisted-plan-executions-{tenantId}`
   - GuardrailEngine evaluates PlanExecution against policies and constraints
   - If approved, ExecutionRouter examines PlanExecution to determine next steps:
     - Extracts `result.next_task_names` from PlanExecution
     - Looks up Task metadata using TaskLookupService
     - Creates TaskInput messages for each next task
   - TaskInput messages are published to `task-inputs-{tenantId}` with original PlanExecution context

### Parent-Child Relationship Field Mappings

| Field | Source | Target | Purpose |
|-------|--------|--------|---------|
| `parent_task_names` | TaskExecution.header.name | PlanExecution.parent_task_names | Links PlanExecution to parent TaskExecutions |
| `header.name` | Plan definition | PlanExecution.header.name | Unique identifier of the plan that created this execution |
| `header.exec_id` | Generated UUID | PlanExecution.header.exec_id | Unique identifier for this specific execution |
| `result.next_task_names` | Plan logic | PlanExecution.result.next_task_names | Determines next tasks in execution graph |

## Parent-Child Relationship Tracking Details

### Implementation in Service Layer

**TaskExecutorService.java**:
- Creates TaskExecution with `parent_plan_exec_id` and `parent_plan_name` fields
- Extracts parent information from PlanExecution.header
- Populates upstream task context from PlanExecution.result.upstream_tasks_results

**PlanExecutorService.java**:
- Creates PlanExecution with `parent_task_names` field (repeated string)
- Builds parent task names list from TaskExecution.header.name
- Populates upstream task results from TaskExecution.result

**ExecutionRouter.java**:
- Routes TaskExecution to PlanExecutor by creating PlanInput with TaskExecution context
- Routes PlanExecution to TaskExecutor by creating TaskInput with PlanExecution context
- Implements graph lookup logic to determine next steps in execution flow

See the actual implementations in:
- `services/task_executor-java/src/main/java/com/pcallahan/agentic/taskexecutor/service/TaskExecutorService.java`
- `services/plan_executor-java/src/main/java/com/pcallahan/agentic/planexecutor/service/PlanExecutorService.java`
- `services/control_plane-java/src/main/java/com/pcallahan/agentic/controlplane/service/ExecutionRouter.java`

### Data Flow Patterns

1. **Forward Flow**: TaskExecution → PlanExecution → TaskExecution (cyclic)
2. **Parent Tracking**: Each execution tracks its immediate parent(s) via dedicated fields
3. **Context Preservation**: Original execution context is passed through the entire flow
4. **Graph Navigation**: ControlPlane uses execution results to determine next steps in graph

### Field Population Examples

**TaskExecution Creation**: TaskExecution objects are created with parent plan tracking fields. See the actual implementation in `services/task_executor-java/src/main/java/com/pcallahan/agentic/taskexecutor/service/TaskExecutorService.java`.

**PlanExecution Creation**: PlanExecution objects are created with parent task tracking fields. See the actual implementation in `services/plan_executor-java/src/main/java/com/pcallahan/agentic/planexecutor/service/PlanExecutorService.java`.

## Protobuf Message Structure

### Protobuf Message Structures

See the actual protobuf definitions in:
- `protos/common.proto`
- `protos/task.proto`
- `protos/plan.proto`

### Simple Protobuf Message Creation Example

```java
// Example: Creating a TaskExecution protobuf message
TaskExecution taskExecution = TaskExecution.newBuilder()
    .setHeader(ExecutionHeader.newBuilder()
        .setName("example_task")
        .setExecId(UUID.randomUUID().toString())
        .setTenantId("tenant123")
        .build())
    .setParentPlanExecId("plan_exec_456")
    .setParentPlanName("example_plan")
    .setResult(TaskResult.newBuilder()
        .setOutput("Task completed successfully")
        .build())
    .build();
```

## Key Changes

1. **ExecutionHeader.id → exec_id**: The execution identifier field has been renamed for clarity
2. **ExecutionHeader.name**: New field to identify the Plan/Task definition that created this execution
3. **TaskExecution.parent_plan_exec_id**: Tracks the execution ID of the parent PlanExecution
4. **TaskExecution.parent_plan_name**: Tracks the name of the parent PlanExecution
5. **PlanExecution.parent_task_names**: Tracks the names of parent TaskExecutions (repeated field)
6. **ControlPlane graph lookup**: ControlPlane now examines TaskExecution and looks up the next Plan in the graph before publishing to PlanExecutor

These changes enable comprehensive parent-child relationship tracking throughout the execution flow, allowing for better debugging, monitoring, and data lineage analysis.

## Topic Architecture

### Data Plane Topics
- `task-executions-{tenantId}` - TaskExecutor publishes TaskExecution protobuf messages
- `plan-executions-{tenantId}` - PlanExecutor publishes PlanExecution protobuf messages

### Control Topics
- `persisted-task-executions-{tenantId}` - DataPlane forwards TaskExecution protobuf messages to ControlPlane
- `persisted-plan-executions-{tenantId}` - DataPlane forwards PlanExecution protobuf messages to ControlPlane

### Control Topics
- `plan-inputs-{tenantId}` - ControlPlane publishes PlanInput protobuf messages (converted from TaskExecution) for PlanExecutor
- `task-inputs-{tenantId}` - ControlPlane publishes TaskInput protobuf messages for TaskExecutor

## Protobuf Message Structures

### [TaskExecution](../protos/task.proto#L30-L42)
### [TaskResult](../protos/task.proto#L9-L30)
### [PlanExecution](../protos/plan.proto#L27-L42)
### [PlanResult](../protos/plan.proto#L9-L27)
### [PlanInput](../protos/plan.proto#L44-L52)

## Output Message Flow from Executors to Data and Control Planes

1. **Task Execution Flow**: Task Executor → Data Plane → Control Plane
2. **Plan Execution Flow**: Plan Executor → Data Plane → Control Plane

## Input Message Flow from Control Plane to Task and Plan Executors

1. **Control Flow**: Data Plane → Control Plane → Executors
2. **Result Flow**: Executors → Data Plane → Control Plane

## Kafka Topics

- **task-executions-{tenantId}**: `TaskExecution` messages (including `TaskResult`) from Task Executor for the Data Plane
- **plan-executions-{tenantId}**: `PlanExecution` messages (including `PlanResult`) from Plan Executor for the Data Plane
- **persisted-task-executions-{tenantId}**: Persisted `TaskExecution` messages from Data Plane to Control Plane
- **persisted-plan-executions-{tenantId}**: Persisted `PlanExecution` messages from Data Plane to Control Plane
- **plan-inputs-{tenantId}**: `PlanInput` messages (with next plan from graph lookup) from Control Plane to the Plan Executor
- **task-inputs-{tenantId}**: `TaskInput` messages from Control Plane to the Task Executor

## Key Implementation Details

### Protobuf Serialization
All services use `ProtobufUtils` for consistent serialization/deserialization with comprehensive error handling:

**Serialization Methods**: The system provides serialization methods for all protobuf message types with validation and error handling.

**Deserialization Methods**: Robust deserialization with proper error handling to prevent message loss.

**Validation**: Built-in message validation ensures data integrity across all services.

**Error Recovery**: Failed serialization/deserialization is handled gracefully with appropriate logging and retry strategies.

**Serialization Strategy**: The system provides robust serialization and deserialization with comprehensive error handling. Failed serialization throws appropriate exceptions with detailed error messages, while deserialization failures are handled gracefully to prevent message loss. The system includes built-in validation and performance monitoring for serialization operations.

### Kafka Configuration
- All producers use `KafkaTemplate<String, byte[]>` for protobuf messages
- All consumers use `ConsumerRecord<String, byte[]>` for protobuf messages
- Topic patterns use tenant-aware routing with `{tenantId}` placeholders

### Error Handling
The system implements comprehensive error handling strategies:

**Deserialization Errors**: Failed protobuf deserialization results in message acknowledgment to prevent infinite retry loops, while logging the error for investigation.

**Guardrail Failures**: Guardrail evaluation failures are logged but don't block message flow, allowing the system to continue processing other messages.

**Database Failures**: Persistence failures are logged but don't prevent message forwarding to downstream services, ensuring the execution flow continues.

**Validation Errors**: Invalid message formats are acknowledged immediately to prevent retry loops.

**Error Handling Strategy**: The system implements comprehensive error handling that distinguishes between different error types. Deserialization errors are acknowledged to prevent infinite retry loops, while processing errors trigger retry mechanisms. Guardrail evaluation failures are logged but don't block message flow, and database failures are logged but don't prevent message forwarding to downstream services.

### Database Persistence
- TaskExecutionEntity and PlanExecutionEntity mirror protobuf structures
- JPA entities include all protobuf fields with appropriate type mappings
- JSON fields store complex protobuf data as serialized JSON strings

## TaskInput Flow

The ControlPlane examines incoming PlanExecutions to extract `result.next_task_names`, looks up Task using the TaskLookupService, and creates TaskInput messages containing the original PlanExecution. This enables more granular task execution control and better separation of concerns between planning and execution phases.

## Benefits of Protobuf Implementation

1. **Type Safety** - Compile-time validation of message structures
2. **Performance** - Efficient binary serialization/deserialization
3. **Schema Evolution** - Backward/forward compatibility for message changes
4. **Consistency** - Uniform message format across all services
5. **Validation** - Built-in message validation and error handling

## Monitoring and Observability

- All services log protobuf message processing with execution IDs
- Kafka topic metrics track message throughput and latency
- Database persistence metrics monitor storage performance
- Guardrail evaluation results are logged for audit trails