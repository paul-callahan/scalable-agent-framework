# Requirements Document

## Introduction

The Agent Graph Composer is a web-based visual editor for creating and managing Agent Graphs in the Agentic Framework. It provides an intuitive drag-and-drop interface for designing agent workflows with tasks and plans, along with integrated file management and code editing capabilities. The application enables users to visually compose directed cyclic graphs of work items while maintaining the underlying Python implementation files for each node.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to visually create agent graphs on a canvas, so that I can design complex agentic workflows without manually writing DOT files.

#### Acceptance Criteria

1. WHEN the user opens the application THEN the system SHALL display a three-pane layout with a left pane taking full height, a center-top pane taking the right 2/3rds and top half, and a center-bottom pane taking the right 2/3rds and bottom half
2. WHEN the application loads THEN the system SHALL display the canvas for drawing agent graphs in the center-top pane
3. WHEN the user selects a task tool from the toolbar THEN the system SHALL allow placing square-shaped task nodes on the canvas
4. WHEN the user selects a plan tool from the toolbar THEN the system SHALL allow placing circle-shaped plan nodes on the canvas
5. WHEN the user selects the edge tool THEN the system SHALL allow drawing directional arrows between nodes that stick to any side of tasks or plans
6. WHEN the user selects nodes or edges THEN the system SHALL provide a way to delete the selected tasks, plans, and edges from the graph canvas
7. WHEN the user creates nodes or edges THEN the system SHALL validate graph constraints in real-time
8. WHEN the canvas content exceeds the viewport THEN the system SHALL provide scrolling and click-drag navigation capabilities
9. WHEN rendering the canvas THEN the system SHALL use tiling for optimized drawing performance

### Requirement 2

**User Story:** As a developer, I want a file explorer interface for managing plan and task implementations, so that I can organize and access the Python code for each node in my graph.

#### Acceptance Criteria

1. WHEN the application loads THEN the system SHALL display a file explorer panel in the left pane
2. WHEN a new graph is created THEN the system SHALL show the agent name as the root node with "plans" and "tasks" folders
3. WHEN a plan node is added to the canvas THEN the system SHALL create a corresponding directory under "plans" with "plan.py" and "requirements.txt" files
4. WHEN a task node is added to the canvas THEN the system SHALL create a corresponding directory under "tasks" with "task.py" and "requirements.txt" files
5. WHEN a user clicks on a node in the canvas THEN the system SHALL expand the corresponding folder in the file explorer
6. WHEN a user clicks on a file in the explorer THEN the system SHALL open the file in the code editor panel
7. WHEN a user clicks on a Python file THEN the system SHALL open it in the code editor using CodeMirror 6 with @codemirror/lang-python plugin
8. WHEN a user clicks on a requirements.txt file THEN the system SHALL open it in the code editor using CodeMirror 6 with default plaintext mode

### Requirement 3

**User Story:** As a developer, I want an integrated code editor for plan and task implementations, so that I can write and modify Python code directly within the visual interface.

#### Acceptance Criteria

1. WHEN the application loads THEN the system SHALL display a code editor panel in the center-bottom pane using CodeMirror 6
2. WHEN a user selects a Python file from the file explorer THEN the system SHALL load the file content into the editor with @codemirror/lang-python language mode
3. WHEN a user selects a requirements.txt file THEN the system SHALL load the file content into the editor with no language mode
4. WHEN a user modifies code in the editor THEN the system SHALL track changes and provide save functionality
5. WHEN a new plan is created THEN the system SHALL generate template "plan.py" code with import "from agentic_common.pb import PlanInput, PlanResult" and the signature "def plan(plan_input: PlanInput) -> PlanResult:"
6. WHEN a new task is created THEN the system SHALL generate template "task.py" code with import "from agentic_common.pb import TaskInput, TaskResult" and the signature "def task(task_input: TaskInput) -> TaskResult:"
7. WHEN files are modified THEN the system SHALL update timestamps and version information

### Requirement 4

**User Story:** As a developer, I want to save and load agent graphs with their associated code files, so that I can persist my work and collaborate with others.

#### Acceptance Criteria

1. WHEN a user saves a graph THEN the system SHALL persist the graph structure and all associated Python files to the backend
2. WHEN saving occurs THEN the system SHALL use AgentGraph, Plan, and Task models from the common-java library
3. WHEN files are saved THEN the system SHALL store them as ExecutorFile objects with name, contents, creation date, version, and update timestamps in a list within Plan and Task objects
4. WHEN the system persists data THEN the system SHALL use Postgres via Spring Data JPA
5. WHEN implementing persistence THEN the system SHALL move AgentGraphEntity, PlanEntity, TaskEntity and their corresponding JPA repositories from graph_builder-java to common-java
6. WHEN moving JPA entities THEN the system SHALL update all existing code that currently uses these entities from graph_builder-java to reference them from common-java
7. WHEN a user loads a graph THEN the system SHALL restore both the visual representation and all associated files
8. WHEN the system processes graphs THEN the system SHALL validate against Agent Graph Specification constraints
9. WHEN multi-tenant operations occur THEN the system SHALL isolate data by tenant ID

### Requirement 5

**User Story:** As a system administrator, I want the application to support multi-tenancy, so that different organizations can use the same deployment while keeping their data isolated.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL provide a tenant ID field in the UI defaulted to "evil-corp"
2. WHEN any backend operation occurs THEN the system SHALL include tenant context for data isolation
3. WHEN graphs are saved or loaded THEN the system SHALL filter results by the current tenant
4. WHEN the system is deployed THEN the system SHALL be prepared for future authentication-based tenant resolution
5. WHEN tenant switching occurs THEN the system SHALL clear the current workspace and load tenant-specific data

### Requirement 6

**User Story:** As a developer, I want the application to validate my agent graphs in real-time, so that I can catch errors early and ensure my graphs follow the specification requirements.

#### Acceptance Criteria

1. WHEN nodes are connected THEN the system SHALL validate that plans only connect to tasks and tasks only connect to plans
2. WHEN a task is created THEN the system SHALL ensure it has exactly one upstream plan
3. WHEN a plan is created THEN the system SHALL allow multiple upstream tasks
4. WHEN node names are entered THEN the system SHALL validate they are unique and valid Python identifiers
5. WHEN the graph is modified THEN the system SHALL check for orphaned nodes and connectivity requirements
6. WHEN validation fails THEN the system SHALL display clear error messages and prevent invalid operations

### Requirement 7

**User Story:** As a developer, I want responsive canvas interactions with smooth performance, so that I can efficiently work with large and complex agent graphs.

#### Acceptance Criteria

1. WHEN the canvas is larger than the viewport THEN the system SHALL provide smooth scrolling with momentum
2. WHEN dragging the canvas THEN the system SHALL provide real-time panning with visual feedback
3. WHEN rendering large graphs THEN the system SHALL use canvas tiling to maintain 60fps performance
4. WHEN nodes are dragged THEN the system SHALL provide smooth movement with edge updates
5. WHEN zooming occurs THEN the system SHALL maintain aspect ratios and center focus appropriately
6. WHEN multiple operations happen simultaneously THEN the system SHALL maintain responsive UI interactions

### Requirement 8

**User Story:** As a developer, I want to list and load existing agent graphs for my tenant, so that I can continue working on previously created graphs.

#### Acceptance Criteria

1. WHEN the application loads THEN the system SHALL provide a way to list existing AgentGraphs for the current tenant ID
2. WHEN a user selects an existing graph from the list THEN the system SHALL load the graph structure and all associated files
3. WHEN loading an existing graph THEN the system SHALL restore the visual canvas representation and populate the file explorer
4. WHEN a user requests to delete an existing graph THEN the system SHALL provide a way to delete AgentGraphs for the current tenant ID
5. WHEN no graphs exist for a tenant THEN the system SHALL provide an option to create a new graph

### Requirement 9

**User Story:** As a developer, I want a responsive single-page application interface, so that I can have a seamless experience while working with agent graphs without page reloads.

#### Acceptance Criteria

1. WHEN the application loads THEN the system SHALL provide a Single Page Application (SPA) interface using React and TypeScript
2. WHEN navigating between different graphs or operations THEN the system SHALL maintain state without full page reloads
3. WHEN performing operations THEN the system SHALL provide real-time updates to the UI without requiring page refreshes
4. WHEN the application encounters errors THEN the system SHALL handle them gracefully within the SPA context

### Requirement 10

**User Story:** As a system administrator, I want the application to be containerized and deployable via Docker, so that I can easily deploy and manage the service in different environments.

#### Acceptance Criteria

1. WHEN deploying the application THEN the system SHALL provide a Dockerfile in services/graph_composer for containerizing the Spring Boot application
2. WHEN setting up the development environment THEN the system SHALL update the docker-compose.yaml in the project root to include the graph_composer service
3. WHEN the container starts THEN the system SHALL serve both the Spring Boot backend and the React frontend from the same container
4. WHEN running in Docker THEN the system SHALL connect to the shared Postgres database for persistence

### Requirement 11

**User Story:** As a developer, I want the build system to follow project conventions and use modern Java, so that the codebase remains consistent and maintainable.

#### Acceptance Criteria

1. WHEN building the project THEN the system SHALL use the pom.xml in the project root as the parent POM
2. WHEN adding dependencies THEN the system SHALL use version properties defined in the parent POM and update version properties for any new dependencies
3. WHEN implementing the backend THEN the system SHALL use Java 21 with latest versions of all dependencies
4. WHEN writing code THEN the system SHALL NOT use Lombok and SHALL follow best development practices
5. WHEN structuring the project THEN the system SHALL follow Spring Boot conventions and maintain clean architecture

### Requirement 12

**User Story:** As a developer, I want comprehensive unit tests with proper database testing, so that I can ensure code quality and reliability.

#### Acceptance Criteria

1. WHEN writing unit tests THEN the system SHALL use TestContainers with Postgres for integration testing
2. WHEN testing service layers THEN the system SHALL use Mockito for mocking dependencies
3. WHEN running tests THEN the system SHALL provide isolated test environments that don't interfere with each other
4. WHEN testing JPA repositories THEN the system SHALL use TestContainers to test against real Postgres instances

### Requirement 13

**User Story:** As a developer, I want a dedicated page to manage all my agent graphs, so that I can view, load, delete, and execute graphs for my tenant.

#### Acceptance Criteria

1. WHEN the user navigates to the graph management page THEN the system SHALL display all AgentGraphs for the current tenant
2. WHEN viewing the graph list THEN the system SHALL show the graph name, creation date, last modified date, and status for each graph
3. WHEN a graph is displayed THEN the system SHALL show its status as one of: New, Running, Stopped, Error
4. WHEN the user selects a graph from the list THEN the system SHALL provide options to load, delete, or submit for execution
5. WHEN the user clicks load THEN the system SHALL navigate to the main editor with the selected graph loaded
6. WHEN the user clicks delete THEN the system SHALL remove the graph after confirmation
7. WHEN the user clicks submit for execution THEN the system SHALL update the graph status (placeholder functionality for now)
8. WHEN no graphs exist for the tenant THEN the system SHALL provide an option to create a new graph