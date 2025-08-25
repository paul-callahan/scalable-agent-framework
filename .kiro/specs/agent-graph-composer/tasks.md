# Implementation Plan

- [x] 1. Set up project structure and core interfaces
  - Create directory structure for services/graph_composer with Spring Boot project layout
  - Set up parent POM reference and configure Java 21 with latest Spring Boot version
  - Define interfaces that establish system boundaries between frontend and backend
  - _Requirements: 11.1, 11.2, 11.3_

- [x] 2. Create ExecutorFile model and enhance existing models
  - [x] 2.1 Create ExecutorFile class in common-java
    - Write ExecutorFile class with name, contents, creation date, version, and update date fields
    - Create unit tests for ExecutorFile model validation
    - _Requirements: 4.3_

  - [x] 2.2 Enhance Plan and Task models with ExecutorFile lists
    - Modify Plan record to include List<ExecutorFile> files field
    - Modify Task record to include List<ExecutorFile> files field
    - Write unit tests for enhanced Plan and Task models
    - _Requirements: 4.3_

- [x] 3. Move and enhance JPA entities in common-java
  - [x] 3.1 Create ExecutorFileEntity JPA entity
    - Write ExecutorFileEntity with proper JPA annotations and relationships
    - Create JPA repository for ExecutorFileEntity
    - Write unit tests using TestContainers for ExecutorFileEntity repository
    - _Requirements: 4.4, 4.5, 12.1, 12.4_

  - [x] 3.2 Move AgentGraphEntity, PlanEntity, TaskEntity to common-java
    - Move entity classes from graph_builder-java to common-java
    - Move corresponding JPA repositories to common-java
    - Add GraphStatus enum and status field to AgentGraphEntity
    - Update package imports and references in existing code
    - _Requirements: 4.5, 4.6, 13.3_

  - [x] 3.3 Enhance PlanEntity and TaskEntity with ExecutorFile relationships
    - Add OneToMany relationship to ExecutorFileEntity in PlanEntity
    - Add OneToMany relationship to ExecutorFileEntity in TaskEntity
    - Write integration tests for entity relationships using TestContainers
    - _Requirements: 4.3, 4.4, 12.1, 12.4_

- [x] 4. Create Spring Boot backend structure
  - [x] 4.1 Set up Spring Boot application and configuration
    - Create main application class with proper Spring Boot annotations
    - Configure application.yml with database connection and JPA settings
    - Set up profiles for development and testing environments
    - _Requirements: 11.1, 11.5_

  - [x] 4.2 Create DTOs for API communication
    - Write AgentGraphDto with status field and all required properties
    - Write AgentGraphSummary DTO for graph listing
    - Write ExecutorFileDto for file operations
    - Create GraphStatus enum (New, Running, Stopped, Error)
    - _Requirements: 13.2, 13.3_

  - [x] 4.3 Implement service layer with business logic
    - Create GraphService for graph CRUD operations with tenant isolation
    - Create FileService for ExecutorFile management
    - Create ValidationService for real-time graph constraint validation
    - Write unit tests using Mockito for service layer
    - _Requirements: 4.7, 5.2, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 12.2_

- [x] 5. Implement REST API controllers
  - [x] 5.1 Create GraphController for graph management
    - Implement endpoints for listing, creating, updating, and deleting graphs
    - Add endpoints for node and edge deletion
    - Implement submit for execution endpoint (placeholder functionality)
    - Add proper error handling and validation
    - Write API tests using MockMvc
    - _Requirements: 1.6, 4.1, 4.2, 8.1, 8.2, 8.4, 13.4, 13.5, 13.6, 13.7_

  - [x] 5.2 Create FileController for file operations
    - Implement endpoints for getting and updating plan/task files
    - Add file content validation and size limits
    - Write API tests for file operations
    - _Requirements: 2.6, 3.4, 3.5, 3.6, 3.7_

  - [x] 5.3 Create ValidationController for real-time validation
    - Implement graph validation endpoint
    - Implement node name validation endpoint
    - Add comprehensive validation rule testing
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 6. Set up React frontend project structure
  - [x] 6.1 Initialize React TypeScript project
    - Set up React project with TypeScript and latest dependencies
    - Configure build system to integrate with Spring Boot static resources
    - Set up ESLint, Prettier, and testing configuration
    - _Requirements: 9.1, 11.3_

  - [x] 6.2 Set up routing and state management
    - Configure React Router for SPA navigation between editor and management views
    - Set up React Context or Redux for application state management
    - Create API client with Axios for backend communication
    - _Requirements: 9.1, 9.2_

  - [x] 6.3 Create base layout and navigation components
    - Implement main three-pane layout component with a left pane taking full height, a center-top pane taking the right 2/3rds and top half, and a center-bottom pane taking the right 2/3rds and bottom half
    - Create navigation between graph management and editor views
    - Add tenant ID input field with "evil-corp" default
    - _Requirements: 1.1, 1.2, 5.1, 9.1_

- [x] 7. Implement graph management page
  - [x] 7.1 Create graph list component
    - Build table/list view showing graph name, creation date, last modified, and status
    - Implement filtering and sorting functionality
    - Add loading states and error handling
    - _Requirements: 13.1, 13.2, 13.3_

  - [x] 7.2 Add graph management actions
    - Implement load graph functionality that navigates to editor
    - Add delete graph with confirmation dialog
    - Create submit for execution button (placeholder functionality)
    - Add create new graph option when no graphs exist
    - _Requirements: 13.4, 13.5, 13.6, 13.7, 13.8_

- [x] 8. Implement file explorer component
  - [x] 8.1 Create tree view file explorer
    - Build hierarchical tree view with agent name as root and plans/tasks folders
    - Implement expand/collapse functionality for folders
    - Add file icons and proper styling
    - _Requirements: 2.1, 2.2_

  - [x] 8.2 Integrate file explorer with canvas selection
    - Auto-expand corresponding folder when node is selected on canvas
    - Highlight selected files and folders
    - Handle file selection and opening in editor
    - _Requirements: 2.5, 2.6_

  - [x] 8.3 Dynamic file creation for new nodes
    - Create plan.py and requirements.txt when plan node is added to canvas
    - Create task.py and requirements.txt when task node is added to canvas
    - Generate template code with proper imports and function signatures
    - _Requirements: 2.3, 2.4, 3.5, 3.6_

- [x] 9. Implement CodeMirror editor integration
  - [x] 9.1 Set up CodeMirror 6 with language support
    - Install and configure CodeMirror 6 with @codemirror/lang-python plugin
    - Set up Python mode for .py files and plaintext mode for requirements.txt
    - Add syntax highlighting and basic editing features
    - _Requirements: 3.1, 3.2, 3.3, 2.7, 2.8_

  - [x] 9.2 Implement file editing and saving
    - Load file content into editor when file is selected
    - Track changes and provide save functionality
    - Update timestamps and version information on save
    - Add unsaved changes warning
    - _Requirements: 3.4, 3.7_

- [x] 10. Create interactive canvas component
  - [x] 10.1 Set up HTML5 Canvas with tiling system
    - Implement canvas rendering with viewport-based tiling for performance
    - Add smooth scrolling and click-drag navigation
    - Set up coordinate system and viewport management
    - _Requirements: 1.7, 1.8, 7.1, 7.2, 7.3_

  - [x] 10.2 Implement toolbar and tool selection
    - Create toolbar with task tool (squares), plan tool (circles), and edge tool
    - Add tool selection state management
    - Implement visual feedback for selected tools
    - _Requirements: 1.3, 1.4, 1.5_

  - [x] 10.3 Add node creation and manipulation
    - Implement task node creation as squares on canvas
    - Implement plan node creation as circles on canvas
    - Add node selection, dragging, and positioning
    - Implement node deletion functionality
    - _Requirements: 1.3, 1.4, 1.6, 7.4_

  - [x] 10.4 Implement edge drawing and management
    - Create directional arrow drawing between nodes
    - Implement edge snapping to any side of tasks or plans
    - Add edge selection and deletion functionality
    - Ensure edges update when nodes are moved
    - _Requirements: 1.5, 1.6, 7.4_

- [x] 11. Add real-time validation system
  - [x] 11.1 Implement graph constraint validation
    - Validate that plans only connect to tasks and tasks only connect to plans
    - Ensure tasks have exactly one upstream plan
    - Allow plans to have multiple upstream tasks
    - Check for orphaned nodes and connectivity requirements
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

  - [x] 11.2 Add node name validation
    - Validate node names are unique across the graph
    - Ensure node names are valid Python identifiers
    - Provide real-time feedback during name entry
    - _Requirements: 6.4_

  - [x] 11.3 Create validation feedback UI
    - Display clear error messages for validation failures
    - Prevent invalid operations from being completed
    - Add visual indicators for validation errors on canvas
    - _Requirements: 6.6_

- [x] 12. Implement performance optimizations
  - [x] 12.1 Add canvas performance optimizations
    - Implement viewport-based rendering for large graphs
    - Add debounced validation to prevent excessive API calls
    - Optimize canvas redraw operations for smooth 60fps performance
    - _Requirements: 7.3, 7.5, 7.6_

  - [x] 12.2 Add backend performance optimizations
    - Implement proper database indexing for tenant queries
    - Add connection pooling configuration
    - Optimize JPA queries for graph loading operations
    - _Requirements: 4.4, 5.2_

- [x] 13. Add comprehensive error handling
  - [x] 13.1 Implement frontend error handling
    - Add global error boundary for React component errors
    - Create API error interceptors with user-friendly messages
    - Add network error handling with retry mechanisms
    - _Requirements: 9.4_

  - [x] 13.2 Create backend exception handling
    - Implement global exception handler for validation errors
    - Add tenant access exception handling
    - Create file processing exception handling
    - _Requirements: 5.2, 5.3_

- [x] 14. Set up testing infrastructure
  - [x] 14.1 Create frontend test suite
    - Set up Jest and React Testing Library for component testing
    - Write unit tests for all major components
    - Add integration tests for canvas interactions
    - _Requirements: 12.1, 12.2, 12.3_

  - [ ] 14.2 Create backend test suite
    - Set up TestContainers with Postgres for integration testing
    - Write unit tests for service layer using Mockito
    - Add API tests using MockMvc
    - Create comprehensive validation rule tests
    - _Requirements: 12.1, 12.2, 12.4_

- [ ] 15. Configure deployment and containerization
  - [ ] 15.1 Create Docker configuration
    - Write Dockerfile for Spring Boot application in services/graph_composer
    - Configure static resource serving for React frontend
    - Set up proper environment variable configuration
    - _Requirements: 10.1, 10.3_

  - [ ] 15.2 Update docker-compose configuration
    - Add graph_composer service to docker-compose.yaml
    - Configure database connection and networking
    - Set up proper service dependencies
    - _Requirements: 10.2, 10.4_

- [ ] 16. Integration testing and final validation
  - [ ] 16.1 End-to-end testing
    - Test complete user workflows from graph creation to execution
    - Validate multi-tenant data isolation
    - Test file management and code editing workflows
    - _Requirements: 4.9, 5.2, 5.5_

  - [ ] 16.2 Performance and load testing
    - Test canvas performance with large graphs
    - Validate database performance under load
    - Test concurrent user scenarios
    - _Requirements: 7.1, 7.2, 7.3, 7.6_

  - [ ] 16.3 Final integration and deployment verification
    - Verify Docker deployment works correctly
    - Test database migrations and schema updates
    - Validate all requirements are met and working
    - _Requirements: 10.1, 10.2, 10.3, 10.4_