package com.pcallahan.agentic.dataplane.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * JPA entity representing a PlanExecution in the database.
 * Mirrors the Python SQLAlchemy PlanExecution model.
 */
@Entity
@Table(name = "plan_executions", indexes = {
    @Index(name = "idx_plan_executions_tenant_id", columnList = "tenant_id"),
    @Index(name = "idx_plan_executions_lifetime_id", columnList = "lifetime_id"),
    @Index(name = "idx_plan_executions_graph_id", columnList = "graph_id"),
    @Index(name = "idx_plan_executions_status", columnList = "status"),
    @Index(name = "idx_plan_executions_created_at", columnList = "created_at"),
    @Index(name = "idx_plan_executions_input_task_id", columnList = "input_task_id")
})
public class PlanExecutionEntity {
    
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
    
    // Plan-specific fields
    @Column(name = "plan_type", length = 100, nullable = false)
    private String planType;
    
    @Column(name = "input_task_id", length = 36)
    private String inputTaskId;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "parameters", columnDefinition = "jsonb")
    private Map<String, Object> parameters;
    
    // Result fields
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "result_next_task_ids", columnDefinition = "jsonb")
    private List<String> resultNextTaskIds;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "result_metadata", columnDefinition = "jsonb")
    private Map<String, Object> resultMetadata;
    
    @Column(name = "error_message", length = 1000)
    private String errorMessage;
    
    @Column(name = "confidence")
    private Double confidence;
    
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
    public PlanExecutionEntity() {
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
    
    public String getPlanType() {
        return planType;
    }
    
    public void setPlanType(String planType) {
        this.planType = planType;
    }
    
    public String getInputTaskId() {
        return inputTaskId;
    }
    
    public void setInputTaskId(String inputTaskId) {
        this.inputTaskId = inputTaskId;
    }
    
    public Map<String, Object> getParameters() {
        return parameters;
    }
    
    public void setParameters(Map<String, Object> parameters) {
        this.parameters = parameters;
    }
    
    public List<String> getResultNextTaskIds() {
        return resultNextTaskIds;
    }
    
    public void setResultNextTaskIds(List<String> resultNextTaskIds) {
        this.resultNextTaskIds = resultNextTaskIds;
    }
    
    public Map<String, Object> getResultMetadata() {
        return resultMetadata;
    }
    
    public void setResultMetadata(Map<String, Object> resultMetadata) {
        this.resultMetadata = resultMetadata;
    }
    
    public String getErrorMessage() {
        return errorMessage;
    }
    
    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }
    
    public Double getConfidence() {
        return confidence;
    }
    
    public void setConfidence(Double confidence) {
        this.confidence = confidence;
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