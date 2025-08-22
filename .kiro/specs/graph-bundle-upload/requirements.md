# Requirements Document

## Introduction

This feature adds file upload capabilities to the services/graph_builder-java service, allowing users to upload tar or zip files containing agent graph definitions. The service will extract, parse, and persist the graph structure while building Docker images for each task and plan component using the executors-py base image.

**Note:** The services/graph_builder-java service already contains functionality for parsing DOT files into AgentGraph, Task, and Plan objects. This existing logic should be leveraged rather than reimplemented.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to upload a compressed file containing my agent graph definition, so that I can deploy my complete graph structure to the system.

#### Acceptance Criteria

1. WHEN a user uploads a tar or zip file THEN the system SHALL accept files with .tar, .tar.gz, .zip extensions
2. WHEN a file is uploaded THEN the system SHALL validate the file size is within acceptable limits (e.g., 100MB)
3. WHEN a file is uploaded THEN the system SHALL require a TENANT_ID parameter in the request
4. WHEN an invalid file format is uploaded THEN the system SHALL return a 400 Bad Request with descriptive error message
5. WHEN TENANT_ID is missing or invalid THEN the system SHALL return a 400 Bad Request error
6. WHEN the upload is successful THEN the system SHALL return a 201 Created status with upload confirmation

### Requirement 2

**User Story:** As a developer, I want the system to extract my uploaded graph bundle, so that the individual components can be processed.

#### Acceptance Criteria

1. WHEN a valid archive is uploaded THEN the system SHALL extract it to a temporary directory
2. WHEN extraction occurs THEN the system SHALL preserve the directory structure from the archive
3. WHEN extraction fails THEN the system SHALL clean up partial extractions and return error response
4. WHEN extraction completes THEN the system SHALL validate required files exist (agent_graph.dot)
5. IF the agent_graph.dot file is missing THEN the system SHALL return a 400 Bad Request error

### Requirement 3

**User Story:** As a developer, I want the system to parse my agent_graph.dot file, so that my graph structure is understood by the system.

#### Acceptance Criteria

1. WHEN agent_graph.dot exists THEN the system SHALL parse it into AgentGraph Java (from services/common-java) instances
2. WHEN parsing occurs THEN the system SHALL create Task and Plan objects from the graph definition
3. WHEN parsing fails due to invalid DOT syntax THEN the system SHALL return a 422 Unprocessable Entity error
4. WHEN parsing succeeds THEN the system SHALL validate graph structure integrity
5. IF graph validation fails THEN the system SHALL return detailed validation error messages

### Requirement 4

**User Story:** As a developer, I want my parsed graph data to be persisted, so that it can be retrieved and used by other system components.

#### Acceptance Criteria

1. WHEN graph parsing succeeds THEN the system SHALL persist AgentGraph entities to the database
2. WHEN persisting occurs THEN the system SHALL store Task and Plan entities with proper relationships
3. WHEN database operations fail THEN the system SHALL rollback all changes and return error response
4. WHEN persistence succeeds THEN the system SHALL return the persisted graph ID
5. IF a graph with the same identifier already exists THEN the system SHALL update the existing graph

### Requirement 5

**User Story:** As a developer, I want Docker images built for my tasks and plans, so that they can be executed in the system.

#### Acceptance Criteria

1. WHEN graph persistence succeeds THEN the DockerImageService SHALL build Docker images for each Task and Plan
2. WHEN building images THEN the DockerImageService SHALL use services/executors-py as the base image
3. WHEN building images THEN the DockerImageService SHALL set TENANT_ID build argument from the API request
4. WHEN building images THEN the DockerImageService SHALL set EXECUTOR_NAME build argument to the task or plan name
5. WHEN building images THEN the DockerImageService SHALL set EXECUTOR_PATH build argument to the path of the copied plan.py or task.py file
6. WHEN building images THEN the DockerImageService SHALL copy the appropriate plan.py or task.py files to the image
7. WHEN building images THEN the DockerImageService SHALL copy requirements.txt files if they exist
8. WHEN image building fails THEN the DockerImageService SHALL log detailed error information and clean up partial builds
9. WHEN all images build successfully THEN the DockerImageService SHALL tag images with appropriate names and save records to database

### Requirement 6

**User Story:** As a developer, I want proper error handling and cleanup, so that failed uploads don't leave the system in an inconsistent state.

#### Acceptance Criteria

1. WHEN any step in the process fails THEN the BundleProcessingService SHALL clean up temporary directories
2. WHEN database operations fail THEN the GraphPersistenceService SHALL rollback all database changes
3. WHEN Docker image building fails THEN the DockerImageService SHALL clean up partial images
4. WHEN cleanup occurs THEN each service SHALL log cleanup actions for debugging
5. WHEN errors occur THEN the ProcessingStatusService SHALL update status and the system SHALL return appropriate HTTP status codes with descriptive messages

### Requirement 7

**User Story:** As a developer, I want to track the progress of my upload processing, so that I know when my graph is ready for use.

#### Acceptance Criteria

1. WHEN upload processing begins THEN the system SHALL return a processing ID
2. WHEN processing occurs THEN the system SHALL log progress at each major step
3. WHEN processing completes THEN the system SHALL update the processing status
4. WHEN processing fails THEN the system SHALL record the failure reason
5. IF processing takes longer than expected THEN the system SHALL provide timeout handling

### Requirement 8

**User Story:** As a developer, I want a web interface to upload agent bundles, so that I can easily deploy my graphs without using API tools directly.

#### Acceptance Criteria

1. WHEN I access the graph-builder service THEN the system SHALL serve a web page for bundle uploads
2. WHEN the web page loads THEN the system SHALL provide a file upload form accepting tar/zip files
3. WHEN the web page loads THEN the system SHALL provide an input field for TENANT_ID
4. WHEN I select a file THEN the system SHALL validate file type before allowing upload
5. WHEN I submit the form THEN the system SHALL call the agent bundle upload API
6. WHEN upload starts THEN the system SHALL show upload progress indication

### Requirement 9

**User Story:** As a developer, I want to monitor the asynchronous processing of my uploaded bundle, so that I can see the status and any errors that occur.

#### Acceptance Criteria

1. WHEN upload completes THEN the system SHALL display the processing status on the web page
2. WHEN processing occurs THEN the system SHALL show real-time status updates for each step
3. WHEN processing steps complete THEN the system SHALL show success indicators for each step
4. WHEN errors occur THEN the system SHALL display detailed error messages as expandable drill-downs
5. WHEN processing completes THEN the system SHALL show final success or failure status
6. WHEN multiple uploads are processed THEN the system SHALL show status for each upload separately

### Requirement 10

**User Story:** As a developer, I want the service layer to follow single responsibility principle, so that the code is maintainable and testable.

#### Acceptance Criteria

1. WHEN implementing the service layer THEN the system SHALL separate concerns into focused service classes within the same Spring Boot application
2. WHEN creating services THEN the BundleProcessingService SHALL handle only file operations and validation
3. WHEN creating services THEN the DockerImageService SHALL handle only Docker image building and management
4. WHEN creating services THEN the GraphPersistenceService SHALL handle only database operations for graphs
5. WHEN creating services THEN the ProcessingStatusService SHALL handle only status tracking and management
6. WHEN creating services THEN the GraphBuilderService SHALL orchestrate the overall process and maintain its core graph parsing responsibilities
7. WHEN services interact THEN they SHALL use dependency injection and clear interfaces
8. WHEN services are tested THEN each service SHALL be unit testable in isolation

### Requirement 11

**User Story:** As a developer, I want consistent styling across admin interfaces, so that the user experience is cohesive.

#### Acceptance Criteria

1. WHEN the web interface is displayed THEN the system SHALL use the same CSS styling as services/admin-java
2. WHEN common resources are needed THEN the system SHALL move shared CSS and web assets to services/common-java
3. WHEN services/common-java contains shared resources THEN both admin-java and graph-builder-java SHALL reference them
4. WHEN styling is applied THEN the system SHALL maintain consistent look and feel across all admin interfaces
5. WHEN shared resources are updated THEN the system SHALL reflect changes in all consuming services