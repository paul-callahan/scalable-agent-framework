package com.pcallahan.agentic.graphcomposer.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Data Transfer Object for complete Agent Graph operations.
 * Contains all information needed for graph editing and management.
 */
public class AgentGraphDto {
    
    private String id;
    
    @NotBlank(message = "Graph name cannot be blank")
    @Size(max = 255, message = "Graph name cannot exceed 255 characters")
    private String name;
    
    @NotBlank(message = "Tenant ID cannot be blank")
    @Size(max = 100, message = "Tenant ID cannot exceed 100 characters")
    private String tenantId;
    
    @NotNull(message = "Graph status cannot be null")
    private GraphStatus status;
    
    private List<PlanDto> plans;
    
    private List<TaskDto> tasks;
    
    private Map<String, Set<String>> planToTasks;
    
    private Map<String, String> taskToPlan;
    
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime createdAt;
    
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime updatedAt;

    public AgentGraphDto() {
    }

    public AgentGraphDto(String id, String name, String tenantId, GraphStatus status, 
                        List<PlanDto> plans, List<TaskDto> tasks, 
                        Map<String, Set<String>> planToTasks, Map<String, String> taskToPlan,
                        LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.id = id;
        this.name = name;
        this.tenantId = tenantId;
        this.status = status;
        this.plans = plans;
        this.tasks = tasks;
        this.planToTasks = planToTasks;
        this.taskToPlan = taskToPlan;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getTenantId() {
        return tenantId;
    }

    public void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }

    public GraphStatus getStatus() {
        return status;
    }

    public void setStatus(GraphStatus status) {
        this.status = status;
    }

    public List<PlanDto> getPlans() {
        return plans;
    }

    public void setPlans(List<PlanDto> plans) {
        this.plans = plans;
    }

    public List<TaskDto> getTasks() {
        return tasks;
    }

    public void setTasks(List<TaskDto> tasks) {
        this.tasks = tasks;
    }

    public Map<String, Set<String>> getPlanToTasks() {
        return planToTasks;
    }

    public void setPlanToTasks(Map<String, Set<String>> planToTasks) {
        this.planToTasks = planToTasks;
    }

    public Map<String, String> getTaskToPlan() {
        return taskToPlan;
    }

    public void setTaskToPlan(Map<String, String> taskToPlan) {
        this.taskToPlan = taskToPlan;
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
}