# Implementation Plan

- [x] 1. Add required dependencies to existing Spring Boot project
  - Add Spring Boot Web and Thymeleaf dependencies to graph_builder-java pom.xml
  - Add Docker Java client dependency for Docker integration
  - Add file upload and multipart handling dependencies
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Move shared web resources to common-java
  - [x] 2.1 Move shared web resources from admin-java to common-java
    - Create src/main/resources/static directory structure in services/common-java
    - Move admin.css from admin-java to common-java as common.css
    - Move admin.js from admin-java to common-java as common.js
    - _Requirements: 10.2, 10.3_

  - [x] 2.2 Update admin-java to reference shared resources
    - Modify admin-java pom.xml to depend on common-java resources
    - Update tenant-admin.html template to reference common.css and common.js
    - Test that admin-java still works with shared resources
    - _Requirements: 10.3, 10.4_

- [x] 3. Create database entities and repositories
  - [x] 3.1 Create GraphBundleEntity with JPA annotations
    - Implement GraphBundleEntity with id, tenantId, graphName, fileName, status, timestamps
    - Add validation annotations and proper indexing
    - Create GraphBundleRepository interface extending JpaRepository
    - _Requirements: 4.1, 4.2, 7.1_

  - [x] 3.2 Create ProcessingStepEntity and repository
    - Implement ProcessingStepEntity with processId, stepName, status, timestamps
    - Create ProcessingStepRepository with custom query methods
    - Add relationship mapping between GraphBundle and ProcessingStep entities
    - _Requirements: 7.2, 7.3, 9.2_

  - [x] 3.3 Create DockerImageEntity and repository
    - Implement DockerImageEntity with processId, imageName, executorType, executorName
    - Create DockerImageRepository with query methods by processId
    - Add proper indexing for efficient queries
    - _Requirements: 5.1, 5.9_

- [x] 4. Add new functionality to existing GraphBuilderService
  - [x] 4.1 Add bundle processing methods to GraphBuilderService
    - Add processBundle method with @Async annotation to existing service
    - Add file validation logic for size and format checking
    - Create temporary directory management with proper cleanup
    - Implement status tracking with ProcessingStep updates
    - _Requirements: 1.1, 1.2, 1.4, 2.1, 6.1_

  - [x] 4.2 Add file extraction logic to GraphBuilderService
    - Add support for tar, tar.gz, and zip file extraction methods
    - Validate extracted directory structure matches expected format
    - Implement proper error handling and cleanup for failed extractions
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 4.3 Add graph persistence methods to GraphBuilderService
    - Add persistGraph method using existing AgentGraph model
    - Add transaction management for atomic graph persistence
    - Create methods for retrieving and listing persisted graphs
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5. Add Docker build functionality to GraphBuilderService
  - [x] 5.1 Add Docker build methods to GraphBuilderService
    - Initialize Docker client with proper configuration in GraphBuilderService
    - Add buildTaskImage method with proper build context setup
    - Add buildPlanImage method with proper build context setup
    - Add error handling and logging for Docker operations
    - _Requirements: 5.1, 5.2, 5.8_

  - [x] 5.2 Implement Dockerfile generation methods in GraphBuilderService
    - Add dynamic Dockerfile generation using services/executors-py as base
    - Set TENANT_ID, EXECUTOR_NAME, and EXECUTOR_PATH build arguments correctly
    - Copy task.py/plan.py files to appropriate paths in the image
    - Copy requirements.txt files when they exist
    - _Requirements: 5.3, 5.4, 5.5, 5.6, 5.7_

  - [x] 5.3 Add Docker image management to GraphBuilderService
    - Implement proper image naming convention with tenant and executor names
    - Add cleanup logic for failed builds and temporary build contexts
    - Implement image listing and status tracking methods
    - _Requirements: 5.9, 6.3_

- [x] 6. Refactor GraphBuilderService into focused service classes
  - [x] 6.1 Create BundleProcessingService
    - Extract file validation, extraction, and cleanup methods from GraphBuilderService
    - Create BundleProcessingService with validateFile, extractBundle, validateExtractedStructure methods
    - Add proper error handling and logging for file operations
    - Update GraphBuilderService to use BundleProcessingService via dependency injection
    - _Requirements: 10.1, 10.2, 2.1, 2.2, 6.1_

  - [x] 6.2 Create DockerImageService
    - Extract Docker client initialization and image building methods from GraphBuilderService
    - Create DockerImageService with buildTaskImage, buildPlanImage, cleanupDockerImages methods
    - Move Dockerfile generation methods to DockerImageService
    - Update GraphBuilderService to use DockerImageService via dependency injection
    - _Requirements: 10.1, 10.3, 5.1, 5.2, 5.8, 5.9_

  - [x] 6.3 Create GraphPersistenceService
    - Extract graph persistence methods from GraphBuilderService
    - Create GraphPersistenceService with persistGraph, getPersistedGraph, listPersistedGraphs methods
    - Add transaction management and proper error handling for database operations
    - Update GraphBuilderService to use GraphPersistenceService via dependency injection
    - _Requirements: 10.1, 10.4, 4.1, 4.2, 4.3, 6.2_

  - [x] 6.4 Create ProcessingStatusService
    - Extract processing status tracking methods from GraphBuilderService
    - Create ProcessingStatusService with createProcessingStep, updateBundleStatus, getProcessingStatus methods
    - Add proper status management and error tracking functionality
    - Update GraphBuilderService to use ProcessingStatusService via dependency injection
    - _Requirements: 10.1, 10.5, 7.2, 7.3, 7.4, 6.5_

  - [x] 6.5 Refactor GraphBuilderService to orchestrate services
    - Remove extracted functionality from GraphBuilderService
    - Update processBundle method to orchestrate the new services
    - Maintain existing buildGraph method as core responsibility
    - Ensure proper dependency injection and error handling between services
    - _Requirements: 10.1, 10.6, 10.7_

- [x] 7. Create REST API controllers
  - [x] 7.1 Implement GraphBundleController for API endpoints
    - Create POST /api/graph-bundle/upload endpoint with file upload handling
    - Add TENANT_ID validation and proper error responses
    - Implement GET /api/graph-bundle/status/{processId} endpoint
    - Add GET /api/graph-bundle/list endpoint for bundle listing
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 7.1_

  - [x] 7.2 Create request/response DTOs
    - Implement BundleUploadRequest with validation annotations
    - Create BundleUploadResponse with processId and status
    - Implement ProcessingStatus DTO with step details and error information
    - Add proper JSON serialization annotations
    - _Requirements: 1.6, 7.1, 7.4, 9.4_

- [x] 8. Implement web interface
  - [x] 8.1 Create GraphBundleWebController for web pages
    - Implement GET /graph-bundle endpoint to serve upload page
    - Add GET /graph-bundle/status endpoint for status monitoring page
    - Configure Thymeleaf template resolution and static resource handling
    - _Requirements: 8.1, 9.1_

  - [x] 8.2 Create graph bundle upload HTML template
    - Design upload form with file input and TENANT_ID field
    - Add client-side file type validation using JavaScript
    - Implement upload progress indication and form submission handling
    - Use common.css styling for consistent look and feel
    - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6, 10.1, 10.4_

  - [x] 8.3 Create status monitoring HTML template
    - Design status display with real-time updates via polling
    - Implement expandable error details as drill-down sections
    - Show processing steps with success/failure indicators
    - Support multiple upload status tracking on same page
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 8.4 Implement graph-bundle.js for client-side functionality
    - Add file upload handling with progress tracking
    - Implement status polling with automatic refresh
    - Create error display and drill-down functionality
    - Add form validation and user feedback mechanisms
    - _Requirements: 8.5, 8.6, 9.2, 9.4_

- [x] 9. Integrate bundle processing with existing graph parsing functionality
  - [x] 9.1 Connect bundle processing to existing buildGraph method
    - Call existing buildGraph method from processBundle method with extracted directory
    - Handle GraphParsingException and GraphValidationException properly
    - Ensure existing DOT file parsing and validation logic is reused
    - _Requirements: 3.1, 3.2, 3.5, 3.6_

  - [x] 9.2 Ensure graph validation integration works with bundles
    - Verify existing graph validation works with bundle processing
    - Ensure Python code bundle validation is applied during bundle processing
    - Handle validation errors with proper status updates
    - _Requirements: 3.4, 3.5_

- [x] 10. Implement error handling and cleanup
  - [x] 10.1 Add comprehensive error handling
    - Implement try-catch blocks for all major operations
    - Create proper HTTP status code responses for different error types
    - Add detailed error logging with correlation IDs
    - _Requirements: 6.5, 1.4, 2.3, 3.3, 5.8_

  - [x] 10.2 Implement cleanup and rollback mechanisms
    - Add temporary directory cleanup in finally blocks
    - Implement database transaction rollback for failed operations
    - Create Docker image cleanup for failed builds
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 11. Add configuration and application properties
  - [x] 11.1 Configure Spring Boot application properties
    - Add multipart file upload configuration with size limits
    - Configure async processing thread pool settings
    - Add Docker client configuration properties
    - Set temporary directory and cleanup settings
    - _Requirements: 1.2, 7.5_

  - [x] 11.2 Add Docker and processing configuration
    - Configure Docker build timeout and concurrent build limits
    - Set base image reference for executors-py
    - Add processing status retention and cleanup settings
    - _Requirements: 5.8, 7.5_

- [x] 12. Create comprehensive tests
  - [x] 12.1 Write unit tests for all service classes
    - Test BundleProcessingService methods with mock file operations
    - Test DockerImageService methods with mock Docker client
    - Test GraphPersistenceService methods with in-memory database
    - Test ProcessingStatusService methods with mock repositories
    - Test refactored GraphBuilderService orchestration logic
    - _Requirements: 10.8, 1.1, 2.1, 3.1, 4.1, 5.1_

  - [x] 12.2 Write integration tests for API endpoints
    - Test file upload endpoint with valid and invalid files
    - Test status endpoint with various processing states
    - Test error handling and proper HTTP status codes
    - Use TestContainers for Docker integration testing
    - _Requirements: 1.4, 1.5, 1.6, 6.5_

  - [x] 12.3 Write web interface tests
    - Test HTML template rendering with Thymeleaf
    - Test JavaScript functionality with mock API responses
    - Test file upload form validation and submission
    - Test status monitoring and error display
    - _Requirements: 8.1, 8.4, 9.1, 9.4_
