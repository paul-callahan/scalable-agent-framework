Prompt:

> Please disregard all prior context.  Read only the @README.md file for context.  I want to create the datamodels for this in an MVP manner.   First we create the base classes ActionTask and PlannerTask.  These are the nodes in the AgentGraph that we'll also create.  We'll use protobuf as the IDL.  The proto files go in proto/ directory.  I also want Python generated for this model.  That python goes in services/standalone-py directory.   Note there is no ActionTask, that is called Task now.  There is no PlannerTask, that is called Plan now.
>
> Only items being passed around should be created in IDL.  This TaskExecution, TaskResult, PlanExecution, PlanResult.   Everything else should be python classes.\
\
> Note also there should be a "tenant_id" field TaskExecution, PlanExecution, AgentGraph, AgentLifetime, Task and Plan.\
\
> you can abstract out an execution header for TaskExecution and PlanExeuction.   We also need control plane and data plane services


I have created the following plan after thorough exploration and analysis of the codebase. Follow the below plan verbatim. Trust the files and references. Do not re-verify what's written in the plan. Explore only when absolutely necessary. First implement all the proposed file changes and then I'll review all the changes together at the end.

### Observations

I explored the repository structure and found it's essentially empty except for documentation files. The README.md provides comprehensive domain model specifications, while design prompt.txt and TODO.md give additional context about the framework's goals. The user wants to create protobuf IDL for data exchange objects (TaskExecution, TaskResult, PlanExecution, PlanResult) while keeping domain logic in Python classes. They specifically need tenant_id fields, an execution header abstraction, and both control/data plane services.

### Approach

I'll create a clean MVP implementation focusing on the core data models and protobuf contracts. The approach will:

1. **Define protobuf schemas** for the four exchange objects with proper field organization
2. **Create execution header abstraction** to avoid duplication between TaskExecution and PlanExecution
3. **Set up Python package structure** with generated protobuf code in the correct location
4. **Implement base Python classes** for Task, Plan, AgentGraph, and AgentLifetime outside the IDL
5. **Add minimal control/data plane service definitions** as gRPC stubs
6. **Include build tooling** for protobuf generation and Python packaging

This keeps the IDL boundary clean while providing a solid foundation for the agentic framework.

### Reasoning

I listed the repository structure and found it mostly empty. I read the README.md which provided comprehensive domain model specifications including entities, execution flow, and architecture. I also read the design prompt.txt and TODO.md files which gave additional context about the framework's conceptual goals and design considerations. The user's requirements align perfectly with the "contract objects" mentioned in TODO.md.

## Mermaid Diagram

sequenceDiagram
participant User as Developer
participant Proto as Protobuf IDL
participant Core as Python Core Classes
participant DataPlane as Data Plane Service
participant ControlPlane as Control Plane Service

    User->>Proto: Define TaskExecution, PlanExecution, TaskResult, PlanResult
    Proto->>Core: Generate Python bindings
    User->>Core: Implement Task, Plan, AgentGraph, AgentLifetime classes
    Core->>Proto: Use protobuf messages for data exchange
    User->>DataPlane: Implement persistence service
    User->>ControlPlane: Implement orchestration service
    DataPlane->>Proto: Accept TaskExecution/PlanExecution messages
    ControlPlane->>Proto: Route execution envelopes
    ControlPlane->>Core: Trigger Task/Plan execution
    Core->>DataPlane: Emit execution records

## Proposed File Changes

### proto(NEW)

Create the proto directory to house all protobuf definition files for the agentic framework IDL.

### proto/common.proto(NEW)

Define the ExecutionHeader message that will be shared between TaskExecution and PlanExecution. Include fields: id (string), parent_id (string), graph_id (string), lifetime_id (string), tenant_id (string), attempt (int32), iteration_idx (int32), created_at (string for ISO-8601), status (enum with PENDING, RUNNING, SUCCEEDED, FAILED), and edge_taken (string). This abstracts common execution metadata as requested by the user.

### proto/task.proto(NEW)

References:

- proto/common.proto(NEW)

Define TaskResult message with a oneof field for either inline data (google.protobuf.Any) or uri (string) for large blob references. Include mime_type (string) and size_bytes (uint64) fields. Also define TaskExecution message that contains ExecutionHeader and TaskResult. Import common.proto for the header definition. This follows the pattern described in the README where large results go to blob storage and small ones are inlined.

### proto/plan.proto(NEW)

References:

- proto/common.proto(NEW)

Define PlanResult message with next_task_ids (repeated string) and optional metadata (map<string,string>). Also define PlanExecution message that contains ExecutionHeader and PlanResult. Import common.proto for the header definition. This captures the planner's decision about which tasks to execute next, as described in the README's logical flow.

### proto/services.proto(NEW)

References:

- proto/task.proto(NEW)
- proto/plan.proto(NEW)

Define gRPC service interfaces for DataPlaneService and ControlPlaneService. DataPlaneService should have PutTaskExecution and PutPlanExecution methods that return simple Ack responses. ControlPlaneService should have methods for guardrail evaluation and orchestration control. Import task.proto and plan.proto for the execution message types. This provides the minimal service contracts mentioned in the README's runtime flow.

### services/standalone-py/agentic(NEW)

Create the main agentic Python package directory.

### services/standalone-py/agentic/__init__.py(NEW)

Create the main package init file. Export the core classes (Task, Plan, AgentGraph, AgentLifetime) and key protobuf types for easy importing. This provides a clean API surface for users of the framework.

### services/standalone-py/agentic/pb(NEW)

Create the pb directory where generated protobuf Python code will be placed. This follows the user's specification for where generated Python protobuf code should go.

### services/standalone-py/agentic/pb/__init__.py(NEW)

Create init file for the pb package. Import and re-export the generated protobuf classes for easier access. This will be populated after protobuf generation.

### services/standalone-py/agentic/core(NEW)

Create the core directory for Python domain classes that are not part of the IDL boundary.

### services/standalone-py/agentic/core/__init__.py(NEW)

Create init file for the core package. Export the main domain classes (Task, Plan, AgentGraph, AgentLifetime, Edge) for easy importing.

### services/standalone-py/agentic/core/task.py(NEW)

References:

- proto/task.proto(NEW)

Implement the Task base class as described in the README. Include tenant_id field, abstract execute method that returns TaskResult protobuf, and methods for serialization/deserialization. The class should be subclassable for custom task types. Include proper typing and async support as mentioned in the extensibility points.

### services/standalone-py/agentic/core/plan.py(NEW)

References:

- proto/plan.proto(NEW)
- proto/task.proto(NEW)

Implement the Plan base class as described in the README. Include tenant_id field, abstract execute method that takes TaskResult and returns PlanResult protobuf with next_task_ids. The class should handle the decision logic for which tasks to execute next. Include proper typing and async support as mentioned in the extensibility points.

### services/standalone-py/agentic/core/graph.py(NEW)

References:

- services/standalone-py/agentic/core/task.py(NEW)
- services/standalone-py/agentic/core/plan.py(NEW)

Implement the AgentGraph class as described in the README. Include tenant_id field, nodes dictionary mapping task IDs to Task/Plan instances, edges configuration with types (NORMAL, PARALLEL, JOIN, FINAL), and semantic versioning. This is the immutable graph template that gets executed. Include validation methods to ensure graph integrity.

### services/standalone-py/agentic/core/lifetime.py(NEW)

References:

- services/standalone-py/agentic/core/graph.py(NEW)

Implement the AgentLifetime class as described in the README. Include tenant_id field, reference to the AgentGraph being executed, current execution state, and methods for pause/resume/abort operations. This represents one runtime instance of an AgentGraph executing to completion. Include state management for tracking execution progress.

### services/standalone-py/agentic/core/edge.py(NEW)

Implement the Edge class as described in the README. Include edge types (NORMAL, PARALLEL, JOIN, FINAL), source and target node IDs, and any conditional logic for edge traversal. This represents the logical links between Tasks and Plans in the graph configuration.

### services/standalone-py/agentic/data_plane(NEW)

Create the data_plane directory for data plane service implementation.

### services/standalone-py/agentic/data_plane/__init__.py(NEW)

Create init file for the data_plane package.

### services/standalone-py/agentic/data_plane/server.py(NEW)

References:

- proto/services.proto(NEW)

Implement a minimal DataPlaneService gRPC server as defined in `services.proto`. Include PutTaskExecution and PutPlanExecution methods that persist executions to storage (SQLite for MVP) and return acknowledgments. This handles the append-only persistence described in the README's runtime flow.

### services/standalone-py/agentic/control_plane(NEW)

Create the control_plane directory for control plane service implementation.

### services/standalone-py/agentic/control_plane/__init__.py(NEW)

Create init file for the control_plane package.

### services/standalone-py/agentic/control_plane/server.py(NEW)

References:

- proto/services.proto(NEW)

Implement a minimal ControlPlaneService gRPC server as defined in `services.proto`. Include methods for guardrail evaluation, orchestration control, and routing execution envelopes to target Plan/Task queues. This handles the deterministic routing and guardrail enforcement described in the README's runtime flow.

### services/standalone-py/pyproject.toml(NEW)

Create a pyproject.toml file for the Python package configuration. Include dependencies for grpcio, grpcio-tools, protobuf, and other required packages. Set up build system configuration and package metadata. Include development dependencies for testing and code quality tools.

### scripts(NEW)

Create scripts directory for build and development utilities.

### scripts/gen_proto.sh(NEW)

References:

- proto/common.proto(NEW)
- proto/task.proto(NEW)
- proto/plan.proto(NEW)
- proto/services.proto(NEW)

Create a shell script to generate Python protobuf code from the proto files. Use grpc_tools.protoc to generate both *_pb2.py and *_pb2_grpc.py files in the `services/standalone-py/agentic/pb/` directory. Include proper import path handling and error checking. This automates the protobuf generation process mentioned in the user requirements.

### Makefile(NEW)

References:

- scripts/gen_proto.sh(NEW)

Create a Makefile with targets for common development tasks: `proto` (generate protobuf code), `install` (install Python dependencies), `test` (run tests), `lint` (run code quality checks), and `clean` (remove generated files). Include proper dependency management and error handling. This provides a convenient interface for the build process.


## Fixup prompts generated by Traycer

Fix the import paths in `proto/task.proto`, `proto/plan.proto`, and `proto/services.proto` by removing the `proto/` prefix from import statements. Change `import "proto/common.proto"` to `import "common.proto"` and similar for other imports.

---

Add `common_pb2` to the imports in `services/standalone-py/agentic/data_plane/server.py`. Update the import statement on line 19 to include `from ..pb import services_pb2, services_pb2_grpc, common_pb2`.

---

Add `common_pb2` to the imports in `services/standalone-py/agentic/data_plane/server.py`. Update the import statement on line 19 to include `from ..pb import services_pb2, services_pb2_grpc, common_pb2`.

---

Make the `from_protobuf` and `deserialize` class methods abstract in both `Task` and `Plan` base classes. Add `@abstractmethod` decorators to these methods and remove their implementations, requiring subclasses to implement their own deserialization logic.

---

Add error handling to the `TaskResult.to_protobuf` method in `services/standalone-py/agentic/core/task.py`. Wrap the `any_msg.Pack(self.data)` call in a try-except block and handle serialization failures gracefully, possibly by converting to JSON first.

---

Enhance graph validation in `services/standalone-py/agentic/core/graph.py` to check for empty graphs and add validation for minimum viable graph structure. Also improve the cycle detection algorithm to handle edge cases like self-loops and complex cycle patterns.

--


