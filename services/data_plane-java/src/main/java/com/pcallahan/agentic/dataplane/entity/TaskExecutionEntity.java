package com.pcallahan.agentic.dataplane.entity;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.Map;

/**
 * JPA entity representing a TaskExecution in the database.
 * Mirrors the Python SQLAlchemy TaskExecution model.
 */
@Entity
@Table(name = "task_executions", indexes = {
    @Index(name = "idx_task_executions_tenant_id", columnList = "tenant_id"),
    @Index(name = "idx_task_executions_lifetime_id", columnList = "lifetime_id"),
    @Index(name = "idx_task_executions_graph_id", columnList = "graph_id"),
    @Index(name = "idx_task_executions_status", columnList = "status"),
    @Index(name = "idx_task_executions_created_at", columnList = "created_at")
})
public class TaskExecutionEntity {
    
    @Id
    @Column(name = "id", length = 36)
    private String id;
    
    @Column(name = "parent_id", length = 36)
    private String parentId;
    
    @Column(name = "graph_id", length = 36, nullable = false)
    private String graphId;
    
    @Column(name = "lifetime_id", length = 36, nullable = false)
    private String lifetimeId;
    
    @Column(name = "tenant_id", length = 50, nullable = false)
    private String tenantId;
    
    @Column(name = "attempt", nullable = false)
    private Integer attempt;
    
    @Column(name = "iteration_idx", nullable = false)
    private Integer iterationIdx;
    
    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status", length = 20, nullable = false)
    private ExecutionStatus status;
    
    @Column(name = "edge_taken", length = 100)
    private String edgeTaken;
    
    // Task-specific fields
    @Column(name = "task_type", length = 100, nullable = false)
    private String taskType;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "parameters", columnDefinition = "jsonb")
    private Map<String, Object> parameters;
    
    // Result fields
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "result_data", columnDefinition = "jsonb")
    private Map<String, Object> resultData;
    
    @Column(name = "result_mime_type", length = 100)
    private String resultMimeType;
    
    @Column(name = "result_size_bytes")
    private Long resultSizeBytes;
    
    @Column(name = "error_message", length = 1000)
    private String errorMessage;
    
    // Auto-managed timestamps
    @Column(name = "db_created_at", nullable = false, updatable = false)
    private Instant dbCreatedAt;
    
    @Column(name = "db_updated_at", nullable = false)
    private Instant dbUpdatedAt;
    
    public enum ExecutionStatus {
        EXECUTION_STATUS_UNSPECIFIED,
        EXECUTION_STATUS_PENDING,
        EXECUTION_STATUS_RUNNING,
        EXECUTION_STATUS_SUCCEEDED,
        EXECUTION_STATUS_FAILED
    }
    
    // Default constructor
    public TaskExecutionEntity() {
        this.dbCreatedAt = Instant.now();
        this.dbUpdatedAt = Instant.now();
    }
    
    // Getters and Setters
    public String getId() {
        return id;
    }
    
    public void setId(String id) {
        this.id = id;
    }
    
    public String getParentId() {
        return parentId;
    }
    
    public void setParentId(String parentId) {
        this.parentId = parentId;
    }
    
    public String getGraphId() {
        return graphId;
    }
    
    public void setGraphId(String graphId) {
        this.graphId = graphId;
    }
    
    public String getLifetimeId() {
        return lifetimeId;
    }
    
    public void setLifetimeId(String lifetimeId) {
        this.lifetimeId = lifetimeId;
    }
    
    public String getTenantId() {
        return tenantId;
    }
    
    public void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }
    
    public Integer getAttempt() {
        return attempt;
    }
    
    public void setAttempt(Integer attempt) {
        this.attempt = attempt;
    }
    
    public Integer getIterationIdx() {
        return iterationIdx;
    }
    
    public void setIterationIdx(Integer iterationIdx) {
        this.iterationIdx = iterationIdx;
    }
    
    public Instant getCreatedAt() {
        return createdAt;
    }
    
    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }
    
    public ExecutionStatus getStatus() {
        return status;
    }
    
    public void setStatus(ExecutionStatus status) {
        this.status = status;
    }
    
    public String getEdgeTaken() {
        return edgeTaken;
    }
    
    public void setEdgeTaken(String edgeTaken) {
        this.edgeTaken = edgeTaken;
    }
    
    public String getTaskType() {
        return taskType;
    }
    
    public void setTaskType(String taskType) {
        this.taskType = taskType;
    }
    
    public Map<String, Object> getParameters() {
        return parameters;
    }
    
    public void setParameters(Map<String, Object> parameters) {
        this.parameters = parameters;
    }
    
    public Map<String, Object> getResultData() {
        return resultData;
    }
    
    public void setResultData(Map<String, Object> resultData) {
        this.resultData = resultData;
    }
    
    public String getResultMimeType() {
        return resultMimeType;
    }
    
    public void setResultMimeType(String resultMimeType) {
        this.resultMimeType = resultMimeType;
    }
    
    public Long getResultSizeBytes() {
        return resultSizeBytes;
    }
    
    public void setResultSizeBytes(Long resultSizeBytes) {
        this.resultSizeBytes = resultSizeBytes;
    }
    
    public String getErrorMessage() {
        return errorMessage;
    }
    
    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }
    
    public Instant getDbCreatedAt() {
        return dbCreatedAt;
    }
    
    public void setDbCreatedAt(Instant dbCreatedAt) {
        this.dbCreatedAt = dbCreatedAt;
    }
    
    public Instant getDbUpdatedAt() {
        return dbUpdatedAt;
    }
    
    public void setDbUpdatedAt(Instant dbUpdatedAt) {
        this.dbUpdatedAt = dbUpdatedAt;
    }
    
    @PreUpdate
    public void preUpdate() {
        this.dbUpdatedAt = Instant.now();
    }
} 