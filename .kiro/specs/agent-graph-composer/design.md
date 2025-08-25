# Design Document

## Overview

The Agent Graph Composer is a web-based visual editor built as a Single Page Application (SPA) using React and TypeScript for the frontend, with a Spring Boot backend. The application provides an intuitive three-pane interface for creating, editing, and managing Agent Graphs in the Agentic Framework. Users can visually design directed cyclic graphs of tasks and plans while simultaneously editing the underlying Python implementation files.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Browser (React SPA)                         │
├─────────────────────────────────────────────────────────────────┤
│  Left Pane        │  Center-Top Pane    │  Center-Bottom Pane  │
│  File Explorer    │  Canvas (Tiled)     │  CodeMirror Editor   │
│                   │  with Toolbar       │                      │
├─────────────────────────────────────────────────────────────────┤
│                    HTTP/REST API                                │
├─────────────────────────────────────────────────────────────────┤
│                Spring Boot Application                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Controllers │  │  Services   │  │ Repositories│            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│                    PostgreSQL Database                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │agent_graphs │  │   plans     │  │   tasks     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend Architecture

The React frontend follows a component-based architecture with clear separation of concerns:

- **Layout Components**: Main three-pane layout management and graph management page
- **Canvas Components**: Interactive graph drawing with HTML5 Canvas and tiling
- **File Explorer Components**: Tree-view file system representation
- **Editor Components**: CodeMirror 6 integration with language support
- **Toolbar Components**: Tool selection and graph operations
- **Graph Management Components**: List view for managing multiple graphs
- **State Management**: React Context/Redux for application state
- **Routing**: React Router for SPA navigation between editor and management views
- **API Layer**: Axios-based HTTP client for backend communication

### Backend Architecture

The Spring Boot backend follows a layered architecture pattern:

- **Controller Layer**: REST endpoints for graph operations, file management, and tenant operations
- **Service Layer**: Business logic for graph validation, file processing, and persistence
- **Repository Layer**: JPA repositories for database operations
- **Entity Layer**: JPA entities moved from graph_builder-java to common-java
- **DTO Layer**: Data transfer objects for API communication
- **Validation Layer**: Real-time graph constraint validation

## Components and Interfaces

### Frontend Components

#### Main Layout Component
```typescript
interface MainLayoutProps {
  tenantId: string;
  onTenantChange: (tenantId: string) => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({ tenantId, onTenantChange }) => {
  // Three-pane layout: left (1/3), center-top (2/3 top), center-bottom (2/3 bottom)
}
```

#### Canvas Component
```typescript
interface CanvasProps {
  graph: AgentGraph;
  selectedTool: ToolType;
  onNodeCreate: (node: Node) => void;
  onEdgeCreate: (edge: Edge) => void;
  onNodeSelect: (nodeId: string) => void;
  onNodeDelete: (nodeId: string) => void;
  onEdgeDelete: (edgeId: string) => void;
}

const GraphCanvas: React.FC<CanvasProps> = ({ graph, selectedTool, onNodeCreate, onEdgeCreate, onNodeSelect, onNodeDelete, onEdgeDelete }) => {
  // Tiled canvas rendering with smooth scrolling and drag support
  // Real-time validation feedback
  // Delete functionality for selected nodes and edges
}
```

#### File Explorer Component
```typescript
interface FileExplorerProps {
  agentName: string;
  plans: Plan[];
  tasks: Task[];
  selectedNodeId?: string;
  onFileSelect: (file: ExecutorFile) => void;
}

const FileExplorer: React.FC<FileExplorerProps> = ({ agentName, plans, tasks, selectedNodeId, onFileSelect }) => {
  // Tree view with expandable folders
  // Auto-expand on node selection
}
```

#### Code Editor Component
```typescript
interface CodeEditorProps {
  file?: ExecutorFile;
  language: 'python' | 'plaintext';
  onChange: (content: string) => void;
  onSave: () => void;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ file, language, onChange, onSave }) => {
  // CodeMirror 6 with @codemirror/lang-python for Python files
  // Default plaintext mode for requirements.txt
}
```

#### Graph Management Component
```typescript
interface GraphManagementProps {
  tenantId: string;
  onGraphSelect: (graphId: string) => void;
  onCreateNew: () => void;
}

interface GraphSummary {
  id: string;
  name: string;
  status: 'New' | 'Running' | 'Stopped' | 'Error';
  createdAt: Date;
  updatedAt: Date;
}

const GraphManagement: React.FC<GraphManagementProps> = ({ tenantId, onGraphSelect, onCreateNew }) => {
  // List view of all graphs for tenant
  // Actions: Load, Delete, Submit for Execution
  // Status display and filtering
}
```

### Backend REST API

#### Graph Management Endpoints
```java
@RestController
@RequestMapping("/api/v1/graphs")
public class GraphController {
    
    @GetMapping
    public ResponseEntity<List<AgentGraphSummary>> listGraphs(@RequestParam String tenantId);
    
    @GetMapping("/{graphId}")
    public ResponseEntity<AgentGraphDto> getGraph(@PathVariable String graphId, @RequestParam String tenantId);
    
    @PostMapping
    public ResponseEntity<AgentGraphDto> createGraph(@RequestBody CreateGraphRequest request);
    
    @PutMapping("/{graphId}")
    public ResponseEntity<AgentGraphDto> updateGraph(@PathVariable String graphId, @RequestBody AgentGraphDto graph);
    
    @DeleteMapping("/{graphId}")
    public ResponseEntity<Void> deleteGraph(@PathVariable String graphId, @RequestParam String tenantId);
    
    @DeleteMapping("/{graphId}/nodes/{nodeId}")
    public ResponseEntity<Void> deleteNode(@PathVariable String graphId, @PathVariable String nodeId, @RequestParam String tenantId);
    
    @DeleteMapping("/{graphId}/edges/{edgeId}")
    public ResponseEntity<Void> deleteEdge(@PathVariable String graphId, @PathVariable String edgeId, @RequestParam String tenantId);
    
    @PostMapping("/{graphId}/execute")
    public ResponseEntity<ExecutionResponse> submitForExecution(@PathVariable String graphId, @RequestParam String tenantId);
    
    @PutMapping("/{graphId}/status")
    public ResponseEntity<Void> updateGraphStatus(@PathVariable String graphId, @RequestBody GraphStatusUpdate statusUpdate);
}
```

#### File Management Endpoints
```java
@RestController
@RequestMapping("/api/v1/files")
public class FileController {
    
    @GetMapping("/plan/{planId}")
    public ResponseEntity<List<ExecutorFileDto>> getPlanFiles(@PathVariable String planId);
    
    @GetMapping("/task/{taskId}")
    public ResponseEntity<List<ExecutorFileDto>> getTaskFiles(@PathVariable String taskId);
    
    @PutMapping("/plan/{planId}/files/{fileName}")
    public ResponseEntity<ExecutorFileDto> updatePlanFile(@PathVariable String planId, @PathVariable String fileName, @RequestBody String content);
    
    @PutMapping("/task/{taskId}/files/{fileName}")
    public ResponseEntity<ExecutorFileDto> updateTaskFile(@PathVariable String taskId, @PathVariable String fileName, @RequestBody String content);
}
```

#### Validation Endpoints
```java
@RestController
@RequestMapping("/api/v1/validation")
public class ValidationController {
    
    @PostMapping("/graph")
    public ResponseEntity<ValidationResult> validateGraph(@RequestBody AgentGraphDto graph);
    
    @PostMapping("/node-name")
    public ResponseEntity<ValidationResult> validateNodeName(@RequestBody NodeNameValidationRequest request);
}
```

## Data Models

### Enhanced Domain Models

#### ExecutorFile Model
```java
public class ExecutorFile {
    private String name;
    private String contents;
    private LocalDateTime creationDate;
    private String version;
    private LocalDateTime updateDate;
    
    // Constructors, getters, setters
}
```

#### Enhanced Plan Model
```java
public record Plan(
    String name, 
    String label, 
    Path planSource, 
    Set<String> upstreamTaskIds,
    List<ExecutorFile> files  // New field for file storage
) {
    // Existing methods plus file management methods
}
```

#### Enhanced Task Model
```java
public record Task(
    String name, 
    String label, 
    Path taskSource, 
    String upstreamPlanId,
    List<ExecutorFile> files  // New field for file storage
) {
    // Existing methods plus file management methods
}
```

### JPA Entities (Moved to common-java)

#### ExecutorFileEntity
```java
@Entity
@Table(name = "executor_files")
public class ExecutorFileEntity {
    @Id
    private String id;
    
    @Column(name = "file_name", nullable = false)
    private String name;
    
    @Lob
    @Column(name = "contents")
    private String contents;
    
    @CreationTimestamp
    @Column(name = "creation_date")
    private LocalDateTime creationDate;
    
    @Column(name = "version")
    private String version;
    
    @UpdateTimestamp
    @Column(name = "update_date")
    private LocalDateTime updateDate;
    
    // Relationships
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "plan_id")
    private PlanEntity plan;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "task_id")
    private TaskEntity task;
    
    // Constructors, getters, setters
}
```

#### Enhanced AgentGraphEntity (Moved to common-java)
```java
@Entity
@Table(name = "agent_graphs")
public class AgentGraphEntity {
    // Existing fields...
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private GraphStatus status = GraphStatus.NEW;
    
    // Existing relationships and methods
}
```

#### Enhanced PlanEntity (Moved to common-java)
```java
@Entity
@Table(name = "plans")
public class PlanEntity {
    // Existing fields...
    
    @OneToMany(mappedBy = "plan", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<ExecutorFileEntity> files = new ArrayList<>();
    
    // Existing methods plus file management
}
```

#### Enhanced TaskEntity (Moved to common-java)
```java
@Entity
@Table(name = "tasks")
public class TaskEntity {
    // Existing fields...
    
    @OneToMany(mappedBy = "task", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<ExecutorFileEntity> files = new ArrayList<>();
    
    // Existing methods plus file management
}
```

### DTOs for API Communication

#### AgentGraphDto
```java
public class AgentGraphDto {
    private String id;
    private String name;
    private String tenantId;
    private GraphStatus status; // New, Running, Stopped, Error
    private List<PlanDto> plans;
    private List<TaskDto> tasks;
    private Map<String, Set<String>> planToTasks;
    private Map<String, String> taskToPlan;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
```

#### AgentGraphSummary
```java
public class AgentGraphSummary {
    private String id;
    private String name;
    private GraphStatus status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
```

#### GraphStatus Enum
```java
public enum GraphStatus {
    NEW,
    RUNNING,
    STOPPED,
    ERROR
}
```

#### ExecutorFileDto
```java
public class ExecutorFileDto {
    private String name;
    private String contents;
    private LocalDateTime creationDate;
    private String version;
    private LocalDateTime updateDate;
}
```

## Error Handling

### Frontend Error Handling
- Global error boundary for React component errors
- API error interceptors with user-friendly messages
- Validation error display in real-time
- Network error handling with retry mechanisms

### Backend Error Handling
```java
@ControllerAdvice
public class GraphComposerExceptionHandler {
    
    @ExceptionHandler(GraphValidationException.class)
    public ResponseEntity<ErrorResponse> handleValidationError(GraphValidationException ex);
    
    @ExceptionHandler(TenantAccessException.class)
    public ResponseEntity<ErrorResponse> handleTenantAccess(TenantAccessException ex);
    
    @ExceptionHandler(FileProcessingException.class)
    public ResponseEntity<ErrorResponse> handleFileProcessing(FileProcessingException ex);
}
```

## Testing Strategy

### Frontend Testing
- **Unit Tests**: Jest and React Testing Library for component testing
- **Integration Tests**: Testing canvas interactions and API integration
- **E2E Tests**: Cypress for full user workflow testing

### Backend Testing
- **Unit Tests**: JUnit 5 with Mockito for service layer testing
- **Integration Tests**: TestContainers with Postgres for repository testing
- **API Tests**: MockMvc for controller testing
- **Validation Tests**: Comprehensive graph validation rule testing

### Test Configuration
```java
@TestConfiguration
public class TestConfig {
    
    @Bean
    @Primary
    @TestScope
    public DataSource testDataSource() {
        return new PostgreSQLContainer<>("postgres:15")
            .withDatabaseName("test_graph_composer")
            .withUsername("test")
            .withPassword("test");
    }
}
```

## Performance Considerations

### Frontend Performance
- **Canvas Tiling**: Implement viewport-based rendering for large graphs
- **Virtual Scrolling**: For file explorer with many files
- **Debounced Validation**: Prevent excessive API calls during editing
- **Code Splitting**: Lazy load components for faster initial load

### Backend Performance
- **Database Indexing**: Proper indexes on tenant_id, graph_name, and foreign keys
- **Connection Pooling**: HikariCP for database connection management
- **Caching**: Redis caching for frequently accessed graphs
- **Pagination**: For graph listing endpoints

## Security Considerations

### Multi-tenancy Security
- Tenant ID validation on all operations
- Row-level security for database queries
- API endpoint authorization based on tenant context

### Input Validation
- Graph structure validation against Agent Graph Specification
- Python code syntax validation
- File size limits for ExecutorFile contents
- XSS protection for user-generated content

## Deployment Configuration

### Docker Configuration
```dockerfile
# services/graph_composer/Dockerfile
FROM openjdk:21-jdk-slim

WORKDIR /app
COPY target/graph-composer-*.jar app.jar
COPY src/main/resources/static /app/static

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### Docker Compose Integration
```yaml
# Addition to docker-compose.yaml
services:
  graph-composer:
    build: ./services/graph_composer
    ports:
      - "8083:8080"
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/agentic_framework
      - SPRING_DATASOURCE_USERNAME=agentic_user
      - SPRING_DATASOURCE_PASSWORD=agentic_password
    depends_on:
      - postgres
    networks:
      - agentic-network
```

This design provides a comprehensive foundation for building the Agent Graph Composer with clear separation of concerns, robust error handling, and scalable architecture patterns.