package com.pcallahan.agentic.graphbuilder.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Entity representing a persisted agent graph with its metadata.
 */
@Entity
@Table(name = "agent_graphs", indexes = {
    @Index(name = "idx_agent_graph_tenant_id", columnList = "tenant_id"),
    @Index(name = "idx_agent_graph_name", columnList = "graph_name"),
    @Index(name = "idx_agent_graph_tenant_name", columnList = "tenant_id, graph_name")
})
public class AgentGraphEntity {

    @Id
    @Column(name = "id", length = 36)
    private String id;

    @NotBlank
    @Size(max = 100)
    @Column(name = "tenant_id", nullable = false, length = 100)
    private String tenantId;

    @NotBlank
    @Size(max = 255)
    @Column(name = "graph_name", nullable = false, length = 255)
    private String graphName;

    @Size(max = 36)
    @Column(name = "process_id", length = 36)
    private String processId;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    // Relationships
    @OneToMany(mappedBy = "agentGraph", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<PlanEntity> plans;

    @OneToMany(mappedBy = "agentGraph", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<TaskEntity> tasks;

    // Default constructor for JPA
    public AgentGraphEntity() {}

    // Constructor for creating new entities
    public AgentGraphEntity(String id, String tenantId, String graphName, String processId) {
        this.id = id;
        this.tenantId = tenantId;
        this.graphName = graphName;
        this.processId = processId;
    }

    // Getters and setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTenantId() {
        return tenantId;
    }

    public void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }

    public String getGraphName() {
        return graphName;
    }

    public void setGraphName(String graphName) {
        this.graphName = graphName;
    }

    public String getProcessId() {
        return processId;
    }

    public void setProcessId(String processId) {
        this.processId = processId;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    public List<PlanEntity> getPlans() {
        return plans;
    }

    public void setPlans(List<PlanEntity> plans) {
        this.plans = plans;
    }

    public List<TaskEntity> getTasks() {
        return tasks;
    }

    public void setTasks(List<TaskEntity> tasks) {
        this.tasks = tasks;
    }
}