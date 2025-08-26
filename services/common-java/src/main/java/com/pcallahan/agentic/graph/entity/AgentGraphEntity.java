package com.pcallahan.agentic.graph.entity;

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
    @Index(name = "idx_agent_graph_name", columnList = "name"),
    @Index(name = "idx_agent_graph_tenant_name", columnList = "tenant_id, name"),
    @Index(name = "idx_agent_graph_status", columnList = "status")
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
    @Column(name = "name", nullable = false, length = 255)
    private String name;


    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private GraphStatus status = GraphStatus.NEW;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
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
    public AgentGraphEntity(String id, String tenantId, String name) {
        this.id = id;
        this.tenantId = tenantId;
        this.name = name;
        this.status = GraphStatus.NEW;
    }

    // Constructor with status
    public AgentGraphEntity(String id, String tenantId, String name, GraphStatus status) {
        this.id = id;
        this.tenantId = tenantId;
        this.name = name;
        this.status = status != null ? status : GraphStatus.NEW;
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

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }


    public GraphStatus getStatus() {
        return status;
    }

    public void setStatus(GraphStatus status) {
        this.status = status != null ? status : GraphStatus.NEW;
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

    @Override
    public String toString() {
        return "AgentGraphEntity{" +
               "id='" + id + '\'' +
               ", tenantId='" + tenantId + '\'' +
               ", name='" + name + '\'' +
               
               ", status=" + status +
               ", createdAt=" + createdAt +
               ", updatedAt=" + updatedAt +
               '}';
    }
}