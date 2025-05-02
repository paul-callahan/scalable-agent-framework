

Prompt:

> Please disregard all prior context.  Read only the @README.md file for context.  I want to create the datamodels for this in an MVP manner.   First we create the base classes ActionTask and PlannerTask.  These are the nodes in the AgentGraph that we'll also create.  We'll use protobuf as the IDL.  The proto files go in proto/ directory.  I also want Python generated for this model.  That python goes in services/standalone-py directory.   Note there is no ActionTask, that is called Task now.  There is no PlannerTask, that is called Plan now.
>
> Only items being passed around should be created in IDL.  This TaskExecution, TaskResult, PlanExecution, PlanResult.   Everything else should be python classes.\
\
> Note also there should be a "tenant_id" field TaskExecution, PlanExecution, AgentGraph, AgentLifetime, Task and Plan.\
\
> you can abstract out an execution header for TaskExecution and PlanExeuction.   We also need control plane and data plane services


## Updated Plan for MVP Datamodels

### Protobuf Files (protos/ directory)

**1. protos/common.proto**
- Common enums: `ExecutionStatus`, `EdgeType`
- Common messages: `Timestamp`, `Duration`, `ResourceUsage`, `BlobReference`
- `ExecutionHeaders` - Abstracted headers for both TaskExecution and PlanExecution

**2. protos/task.proto**
- `TaskExecution` - Record of a single Task run with tenant_id, ExecutionHeaders, telemetry, and TaskResult
- `TaskResult` - Structured output from any task type (inline content or blob reference)
- `PolicyTelemetry` - tokens_used, cost_usd, latency_ms for guardrails

**3. protos/plan.proto**
- `PlanExecution` - Record of a single Plan run with tenant_id, ExecutionHeaders, telemetry, and PlanResult
- `PlanResult` - Structured output from any plan type with next_task_ids[]

### Python Classes (services/standalone-py/)

**1. Core Graph Entities**
- `Task` - Node that performs work (API call, DB query, computation) with tenant_id
- `Plan` - Node that selects next Task based on rules or prior state with tenant_id
- `AgentGraph` - Immutable graph template with nodes and edges, tenant_id
- `AgentLifetime` - Runtime instance of an AgentGraph executing to completion, tenant_id
- `Edge` - Logical link between Tasks and Plans with configuration

**2. Configuration Classes**
- `TaskConfiguration` - Task-specific settings and parameters
- `PlanConfiguration` - Plan-specific rules, conditions, and routing logic
- `GraphMetadata` - Versioning, description, and graph-level configuration

**3. Supporting Classes**
- `GraphNode` - Union type containing either Task or Plan
- `RoutingRule` - Condition and corresponding next task
- `EdgeConfiguration` - Edge-specific settings
- `JoinConfiguration` - How multiple parallel paths should join

### Control Plane Services (services/control-plane/)

**1. Guardrail Engine**
- `GuardrailEngine` - Evaluates YAML policies against execution telemetry
- `PolicyEvaluator` - Checks cost, safety, and iteration caps
- `ExecutionController` - Issues REJECT_EXECUTION, PAUSE_LIFETIME, ABORT_LIFETIME events

**2. Orchestration Services**
- `GraphOrchestrator` - Manages AgentLifetime execution flow
- `TaskRouter` - Routes TaskExecutions to appropriate Plan executors
- `PlanRouter` - Routes PlanExecutions to appropriate Task executors

### Data Plane Services (services/data-plane/)

**1. State Management**
- `StateStore` - Append-only persistence of TaskExecution and PlanExecution records
- `ExecutionRepository` - CRUD operations for execution records
- `LifetimeRepository` - CRUD operations for AgentLifetime records

**2. Event Management**
- `EventBus` - Publishes execution events to Control Plane
- `ExecutionPublisher` - Publishes TaskExecution and PlanExecution events
- `ReferencePublisher` - Publishes lightweight reference messages

**3. Blob Management**
- `BlobStore` - Stores large results referenced by URI
- `BlobManager` - Handles blob storage operations (FS/S3)

### Build Configuration

**1. protos/buf.yaml**
- Buf configuration for protobuf management
- Lint rules and breaking change detection

**2. protos/buf.gen.yaml**
- Python code generation configuration
- Output to services/standalone-py/

**3. Makefile**
- `proto-gen` - Generate Python code from protobuf
- `proto-lint` - Lint protobuf files
- `proto-clean` - Clean generated files

### Key Design Decisions

1. **Root-level protos/ directory**: All protobuf files in `protos/`
2. **Separated execution protos**: Task-related in `task.proto`, Plan-related in `plan.proto`
3. **Abstracted ExecutionHeaders**: Shared between TaskExecution and PlanExecution for consistency
4. **Control Plane Services**: Guardrail enforcement, orchestration, and routing
5. **Data Plane Services**: State persistence, event publishing, and blob management
6. **Tenant isolation**: tenant_id field in all relevant entities
7. **BlobReference pattern**: Handle large results via URI references, small results inlined
8. **Extensible configuration**: JSON strings for task/plan specific configs
9. **Semantic versioning**: For AgentGraph templates
10. **Execution tracking**: Full provenance with headers, telemetry, and iteration support

This architecture supports the multitenant cloud deployment described in the README, with clear separation between control plane (guardrails, orchestration) and data plane (persistence, events) services, and organized protobuf definitions in the root-level `protos/` directory.