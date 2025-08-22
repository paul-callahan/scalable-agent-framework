package com.pcallahan.agentic.graphbuilder.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;

/**
 * Entity representing a persisted plan within an agent graph.
 */
@Entity
@Table(name = "plans", indexes = {
    @Index(name = "idx_plan_graph_id", columnList = "graph_id"),
    @Index(name = "idx_plan_name", columnList = "plan_name"),
    @Index(name = "idx_plan_graph_name", columnList = "graph_id, plan_name")
})
public class PlanEntity {

    @Id
    @Column(name = "id", length = 36)
    private String id;

    @NotBlank
    @Size(max = 255)
    @Column(name = "plan_name", nullable = false, length = 255)
    private String planName;

    @Size(max = 255)
    @Column(name = "label", length = 255)
    private String label;

    @Size(max = 500)
    @Column(name = "plan_source_path", length = 500)
    private String planSourcePath;

    // Relationship to AgentGraphEntity
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "graph_id", nullable = false)
    private AgentGraphEntity agentGraph;

    // Relationships to tasks
    @OneToMany(mappedBy = "upstreamPlan", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<TaskEntity> downstreamTasks;

    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(
        name = "plan_upstream_tasks",
        joinColumns = @JoinColumn(name = "plan_id"),
        inverseJoinColumns = @JoinColumn(name = "task_id")
    )
    private List<TaskEntity> upstreamTasks;

    // Default constructor for JPA
    public PlanEntity() {}

    // Constructor for creating new entities
    public PlanEntity(String id, String planName, String label, String planSourcePath, AgentGraphEntity agentGraph) {
        this.id = id;
        this.planName = planName;
        this.label = label;
        this.planSourcePath = planSourcePath;
        this.agentGraph = agentGraph;
    }

    // Getters and setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getPlanName() {
        return planName;
    }

    public void setPlanName(String planName) {
        this.planName = planName;
    }

    public String getLabel() {
        return label;
    }

    public void setLabel(String label) {
        this.label = label;
    }

    public String getPlanSourcePath() {
        return planSourcePath;
    }

    public void setPlanSourcePath(String planSourcePath) {
        this.planSourcePath = planSourcePath;
    }

    public AgentGraphEntity getAgentGraph() {
        return agentGraph;
    }

    public void setAgentGraph(AgentGraphEntity agentGraph) {
        this.agentGraph = agentGraph;
    }

    public List<TaskEntity> getDownstreamTasks() {
        return downstreamTasks;
    }

    public void setDownstreamTasks(List<TaskEntity> downstreamTasks) {
        this.downstreamTasks = downstreamTasks;
    }

    public List<TaskEntity> getUpstreamTasks() {
        return upstreamTasks;
    }

    public void setUpstreamTasks(List<TaskEntity> upstreamTasks) {
        this.upstreamTasks = upstreamTasks;
    }
}