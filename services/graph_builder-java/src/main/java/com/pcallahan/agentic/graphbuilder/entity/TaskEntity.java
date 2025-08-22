package com.pcallahan.agentic.graphbuilder.entity;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;

/**
 * Entity representing a persisted task within an agent graph.
 */
@Entity
@Table(name = "tasks", indexes = {
    @Index(name = "idx_task_graph_id", columnList = "graph_id"),
    @Index(name = "idx_task_name", columnList = "task_name"),
    @Index(name = "idx_task_graph_name", columnList = "graph_id, task_name"),
    @Index(name = "idx_task_upstream_plan", columnList = "upstream_plan_id")
})
public class TaskEntity {

    @Id
    @Column(name = "id", length = 36)
    private String id;

    @NotBlank
    @Size(max = 255)
    @Column(name = "task_name", nullable = false, length = 255)
    private String taskName;

    @Size(max = 255)
    @Column(name = "label", length = 255)
    private String label;

    @Size(max = 500)
    @Column(name = "task_source_path", length = 500)
    private String taskSourcePath;

    // Relationship to AgentGraphEntity
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "graph_id", nullable = false)
    private AgentGraphEntity agentGraph;

    // Relationship to upstream plan
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "upstream_plan_id")
    private PlanEntity upstreamPlan;

    // Relationship to downstream plans
    @ManyToMany(mappedBy = "upstreamTasks", fetch = FetchType.LAZY)
    private List<PlanEntity> downstreamPlans;

    // Default constructor for JPA
    public TaskEntity() {}

    // Constructor for creating new entities
    public TaskEntity(String id, String taskName, String label, String taskSourcePath, 
                     AgentGraphEntity agentGraph, PlanEntity upstreamPlan) {
        this.id = id;
        this.taskName = taskName;
        this.label = label;
        this.taskSourcePath = taskSourcePath;
        this.agentGraph = agentGraph;
        this.upstreamPlan = upstreamPlan;
    }

    // Getters and setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTaskName() {
        return taskName;
    }

    public void setTaskName(String taskName) {
        this.taskName = taskName;
    }

    public String getLabel() {
        return label;
    }

    public void setLabel(String label) {
        this.label = label;
    }

    public String getTaskSourcePath() {
        return taskSourcePath;
    }

    public void setTaskSourcePath(String taskSourcePath) {
        this.taskSourcePath = taskSourcePath;
    }

    public AgentGraphEntity getAgentGraph() {
        return agentGraph;
    }

    public void setAgentGraph(AgentGraphEntity agentGraph) {
        this.agentGraph = agentGraph;
    }

    public PlanEntity getUpstreamPlan() {
        return upstreamPlan;
    }

    public void setUpstreamPlan(PlanEntity upstreamPlan) {
        this.upstreamPlan = upstreamPlan;
    }

    public List<PlanEntity> getDownstreamPlans() {
        return downstreamPlans;
    }

    public void setDownstreamPlans(List<PlanEntity> downstreamPlans) {
        this.downstreamPlans = downstreamPlans;
    }
}