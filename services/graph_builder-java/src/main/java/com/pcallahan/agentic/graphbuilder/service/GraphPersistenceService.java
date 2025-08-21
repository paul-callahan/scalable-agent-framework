package com.pcallahan.agentic.graphbuilder.service;

import com.pcallahan.agentic.graph.model.AgentGraph;
import com.pcallahan.agentic.graph.model.Plan;
import com.pcallahan.agentic.graph.model.Task;
import com.pcallahan.agentic.graphbuilder.entity.AgentGraphEntity;
import com.pcallahan.agentic.graphbuilder.entity.PlanEntity;
import com.pcallahan.agentic.graphbuilder.entity.TaskEntity;
import com.pcallahan.agentic.graphbuilder.exception.GraphPersistenceException;
import com.pcallahan.agentic.graphbuilder.repository.AgentGraphRepository;
import com.pcallahan.agentic.graphbuilder.repository.PlanRepository;
import com.pcallahan.agentic.graphbuilder.repository.TaskRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Service responsible for persisting and retrieving agent graphs from the database.
 */
@Service
public class GraphPersistenceService {
    
    private static final Logger logger = LoggerFactory.getLogger(GraphPersistenceService.class);
    
    private final AgentGraphRepository agentGraphRepository;
    private final PlanRepository planRepository;
    private final TaskRepository taskRepository;
    
    @Autowired
    public GraphPersistenceService(AgentGraphRepository agentGraphRepository,
                                  PlanRepository planRepository,
                                  TaskRepository taskRepository) {
        this.agentGraphRepository = agentGraphRepository;
        this.planRepository = planRepository;
        this.taskRepository = taskRepository;
    }
    
    /**
     * Persists an AgentGraph to the database with transaction management.
     * 
     * @param graph The AgentGraph to persist
     * @param tenantId The tenant ID
     * @param processId The process ID (optional)
     * @return The ID of the persisted graph
     * @throws GraphPersistenceException if persistence fails
     */
    @Transactional
    public String persistGraph(AgentGraph graph, String tenantId, String processId) {
        String correlationId = getOrCreateCorrelationId();
        
        try {
            logger.info("Persisting agent graph '{}' for tenant {} [correlationId={}]", graph.name(), tenantId, correlationId);
            
            // Validate inputs
            if (graph == null) {
                throw new GraphPersistenceException("Graph cannot be null", correlationId, null);
            }
            if (tenantId == null || tenantId.trim().isEmpty()) {
                throw new GraphPersistenceException("Tenant ID cannot be null or empty", correlationId, graph.name());
            }
            
            // Check if graph already exists and delete it
            Optional<AgentGraphEntity> existingGraph = agentGraphRepository.findByTenantIdAndGraphName(tenantId, graph.name());
            if (existingGraph.isPresent()) {
                logger.info("Updating existing graph '{}' for tenant {} [correlationId={}]", graph.name(), tenantId, correlationId);
                deleteGraphData(existingGraph.get().getId());
            }
            
            // Create new graph entity
            String graphId = UUID.randomUUID().toString();
            AgentGraphEntity graphEntity = new AgentGraphEntity(graphId, tenantId, graph.name(), processId);
            agentGraphRepository.save(graphEntity);
            logger.debug("Created graph entity with ID {} [correlationId={}]", graphId, correlationId);
            
            // Create plan entities
            Map<String, PlanEntity> planEntityMap = new HashMap<>();
            for (Plan plan : graph.plans().values()) {
                try {
                    String planId = UUID.randomUUID().toString();
                    PlanEntity planEntity = new PlanEntity(
                        planId, 
                        plan.name(), 
                        plan.label(), 
                        plan.planSource().toString(), 
                        graphEntity
                    );
                    planRepository.save(planEntity);
                    planEntityMap.put(plan.name(), planEntity);
                    logger.debug("Created plan entity '{}' [correlationId={}]", plan.name(), correlationId);
                } catch (Exception e) {
                    logger.error("Failed to create plan entity '{}' [correlationId={}]: {}", plan.name(), correlationId, e.getMessage(), e);
                    throw new GraphPersistenceException("Failed to persist plan '" + plan.name() + "': " + e.getMessage(), e, correlationId, graph.name());
                }
            }
            
            // Create task entities
            Map<String, TaskEntity> taskEntityMap = new HashMap<>();
            for (Task task : graph.tasks().values()) {
                try {
                    String taskId = UUID.randomUUID().toString();
                    PlanEntity upstreamPlan = planEntityMap.get(task.upstreamPlanId());
                    
                    TaskEntity taskEntity = new TaskEntity(
                        taskId,
                        task.name(),
                        task.label(),
                        task.taskSource().toString(),
                        graphEntity,
                        upstreamPlan
                    );
                    taskRepository.save(taskEntity);
                    taskEntityMap.put(task.name(), taskEntity);
                    logger.debug("Created task entity '{}' [correlationId={}]", task.name(), correlationId);
                } catch (Exception e) {
                    logger.error("Failed to create task entity '{}' [correlationId={}]: {}", task.name(), correlationId, e.getMessage(), e);
                    throw new GraphPersistenceException("Failed to persist task '" + task.name() + "': " + e.getMessage(), e, correlationId, graph.name());
                }
            }
            
            // Update plan-task relationships
            updatePlanTaskRelationships(graph, planEntityMap, taskEntityMap);
            
            logger.info("Successfully persisted agent graph '{}' with ID {} [correlationId={}]", graph.name(), graphId, correlationId);
            return graphId;
            
        } catch (GraphPersistenceException e) {
            logger.error("Graph persistence failed [correlationId={}]: {}", correlationId, e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("Unexpected error during graph persistence [correlationId={}]: {}", correlationId, e.getMessage(), e);
            throw new GraphPersistenceException("Failed to persist graph: " + e.getMessage(), e, correlationId, graph != null ? graph.name() : null);
        }
    }
    
    /**
     * Retrieves a persisted AgentGraph by ID.
     * 
     * @param graphId The graph ID
     * @return The AgentGraph
     * @throws GraphPersistenceException if retrieval fails
     */
    @Transactional(readOnly = true)
    public AgentGraph getPersistedGraph(String graphId) {
        String correlationId = getOrCreateCorrelationId();
        
        try {
            logger.debug("Retrieving persisted graph with ID {} [correlationId={}]", graphId, correlationId);
            
            if (graphId == null || graphId.trim().isEmpty()) {
                throw new GraphPersistenceException("Graph ID cannot be null or empty", correlationId, null);
            }
            
            Optional<AgentGraphEntity> graphEntityOpt = agentGraphRepository.findById(graphId);
            if (graphEntityOpt.isEmpty()) {
                throw new GraphPersistenceException("Graph not found with ID: " + graphId, correlationId, null);
            }
            
            AgentGraph graph = convertToAgentGraph(graphEntityOpt.get());
            logger.debug("Successfully retrieved graph '{}' [correlationId={}]", graph.name(), correlationId);
            return graph;
            
        } catch (GraphPersistenceException e) {
            logger.error("Failed to retrieve graph with ID {} [correlationId={}]: {}", graphId, correlationId, e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("Unexpected error retrieving graph with ID {} [correlationId={}]: {}", graphId, correlationId, e.getMessage(), e);
            throw new GraphPersistenceException("Failed to retrieve graph: " + e.getMessage(), e, correlationId, null);
        }
    }
    
    /**
     * Lists all persisted graphs for a tenant.
     * 
     * @param tenantId The tenant ID
     * @return List of graph information
     * @throws GraphPersistenceException if listing fails
     */
    @Transactional(readOnly = true)
    public List<GraphInfo> listPersistedGraphs(String tenantId) {
        String correlationId = getOrCreateCorrelationId();
        
        try {
            logger.debug("Listing persisted graphs for tenant {} [correlationId={}]", tenantId, correlationId);
            
            if (tenantId == null || tenantId.trim().isEmpty()) {
                throw new GraphPersistenceException("Tenant ID cannot be null or empty", correlationId, null);
            }
            
            List<AgentGraphEntity> graphEntities = agentGraphRepository.findByTenantIdOrderByCreatedAtDesc(tenantId);
            
            List<GraphInfo> result = graphEntities.stream()
                .map(entity -> new GraphInfo(
                    entity.getId(),
                    entity.getGraphName(),
                    entity.getTenantId(),
                    entity.getCreatedAt(),
                    entity.getUpdatedAt(),
                    entity.getProcessId()
                ))
                .collect(Collectors.toList());
                
            logger.debug("Found {} graphs for tenant {} [correlationId={}]", result.size(), tenantId, correlationId);
            return result;
            
        } catch (GraphPersistenceException e) {
            logger.error("Failed to list graphs for tenant {} [correlationId={}]: {}", tenantId, correlationId, e.getMessage());
            throw e;
        } catch (Exception e) {
            logger.error("Unexpected error listing graphs for tenant {} [correlationId={}]: {}", tenantId, correlationId, e.getMessage(), e);
            throw new GraphPersistenceException("Failed to list graphs: " + e.getMessage(), e, correlationId, null);
        }
    }
    
    /**
     * Updates the relationships between plans and tasks.
     */
    private void updatePlanTaskRelationships(AgentGraph graph, 
                                           Map<String, PlanEntity> planEntityMap, 
                                           Map<String, TaskEntity> taskEntityMap) {
        String correlationId = getOrCreateCorrelationId();
        
        try {
            logger.debug("Updating plan-task relationships [correlationId={}]", correlationId);
            
            // Update plan upstream tasks
            for (Plan plan : graph.plans().values()) {
                try {
                    PlanEntity planEntity = planEntityMap.get(plan.name());
                    List<TaskEntity> upstreamTasks = plan.upstreamTaskIds().stream()
                        .map(taskEntityMap::get)
                        .filter(Objects::nonNull)
                        .collect(Collectors.toList());
                    planEntity.setUpstreamTasks(upstreamTasks);
                    planRepository.save(planEntity);
                } catch (Exception e) {
                    logger.error("Failed to update relationships for plan '{}' [correlationId={}]: {}", plan.name(), correlationId, e.getMessage(), e);
                    throw new GraphPersistenceException("Failed to update relationships for plan '" + plan.name() + "': " + e.getMessage(), e, correlationId, graph.name());
                }
            }
            
            logger.debug("Successfully updated plan-task relationships for {} plans and {} tasks [correlationId={}]", 
                planEntityMap.size(), taskEntityMap.size(), correlationId);
                
        } catch (GraphPersistenceException e) {
            throw e;
        } catch (Exception e) {
            logger.error("Unexpected error updating plan-task relationships [correlationId={}]: {}", correlationId, e.getMessage(), e);
            throw new GraphPersistenceException("Failed to update plan-task relationships: " + e.getMessage(), e, correlationId, graph.name());
        }
    }
    
    /**
     * Deletes existing graph data for updates.
     */
    private void deleteGraphData(String graphId) {
        String correlationId = getOrCreateCorrelationId();
        
        try {
            logger.debug("Deleting existing graph data for graph ID {} [correlationId={}]", graphId, correlationId);
            
            // Delete related entities in proper order
            taskRepository.deleteByAgentGraphId(graphId);
            planRepository.deleteByAgentGraphId(graphId);
            agentGraphRepository.deleteById(graphId);
            
            logger.debug("Successfully deleted existing graph data for graph ID {} [correlationId={}]", graphId, correlationId);
            
        } catch (Exception e) {
            logger.error("Failed to delete existing graph data for graph ID {} [correlationId={}]: {}", graphId, correlationId, e.getMessage(), e);
            throw new GraphPersistenceException("Failed to delete existing graph data: " + e.getMessage(), e, correlationId, null);
        }
    }
    
    /**
     * Converts an AgentGraphEntity to an AgentGraph domain object.
     */
    private AgentGraph convertToAgentGraph(AgentGraphEntity entity) {
        // Load plans
        List<PlanEntity> planEntities = planRepository.findByAgentGraphId(entity.getId());
        Map<String, Plan> plans = planEntities.stream()
            .collect(Collectors.toMap(
                PlanEntity::getPlanName,
                this::convertToPlan
            ));
        
        // Load tasks
        List<TaskEntity> taskEntities = taskRepository.findByAgentGraphId(entity.getId());
        Map<String, Task> tasks = taskEntities.stream()
            .collect(Collectors.toMap(
                TaskEntity::getTaskName,
                this::convertToTask
            ));
        
        // Build relationships
        Map<String, Set<String>> planToTasks = new HashMap<>();
        Map<String, String> taskToPlan = new HashMap<>();
        
        for (TaskEntity taskEntity : taskEntities) {
            if (taskEntity.getUpstreamPlan() != null) {
                String planName = taskEntity.getUpstreamPlan().getPlanName();
                String taskName = taskEntity.getTaskName();
                
                planToTasks.computeIfAbsent(planName, k -> new HashSet<>()).add(taskName);
                taskToPlan.put(taskName, planName);
            }
        }
        
        return new AgentGraph(entity.getGraphName(), plans, tasks, planToTasks, taskToPlan);
    }
    
    /**
     * Converts a PlanEntity to a Plan domain object.
     */
    private Plan convertToPlan(PlanEntity entity) {
        Set<String> upstreamTaskIds = entity.getUpstreamTasks().stream()
            .map(TaskEntity::getTaskName)
            .collect(Collectors.toSet());
        
        return new Plan(
            entity.getPlanName(),
            entity.getLabel(),
            Path.of(entity.getPlanSourcePath()),
            upstreamTaskIds
        );
    }
    
    /**
     * Converts a TaskEntity to a Task domain object.
     */
    private Task convertToTask(TaskEntity entity) {
        String upstreamPlanId = entity.getUpstreamPlan() != null ? 
            entity.getUpstreamPlan().getPlanName() : null;
        
        return new Task(
            entity.getTaskName(),
            entity.getLabel(),
            Path.of(entity.getTaskSourcePath()),
            upstreamPlanId
        );
    }
    
    /**
     * Information about a persisted graph.
     */
    public static class GraphInfo {
        private final String id;
        private final String name;
        private final String tenantId;
        private final LocalDateTime createdAt;
        private final LocalDateTime updatedAt;
        private final String processId;
        
        public GraphInfo(String id, String name, String tenantId, LocalDateTime createdAt, 
                        LocalDateTime updatedAt, String processId) {
            this.id = id;
            this.name = name;
            this.tenantId = tenantId;
            this.createdAt = createdAt;
            this.updatedAt = updatedAt;
            this.processId = processId;
        }
        
        public String getId() { return id; }
        public String getName() { return name; }
        public String getTenantId() { return tenantId; }
        public LocalDateTime getCreatedAt() { return createdAt; }
        public LocalDateTime getUpdatedAt() { return updatedAt; }
        public String getProcessId() { return processId; }
        
        @Override
        public String toString() {
            return "GraphInfo{" +
                "id='" + id + '\'' +
                ", name='" + name + '\'' +
                ", tenantId='" + tenantId + '\'' +
                ", createdAt=" + createdAt +
                ", updatedAt=" + updatedAt +
                ", processId='" + processId + '\'' +
                '}';
        }
    }
    
    /**
     * Gets or creates a correlation ID for error tracking.
     */
    private String getOrCreateCorrelationId() {
        String mdcId = MDC.get("correlationId");
        if (mdcId != null && !mdcId.trim().isEmpty()) {
            return mdcId;
        }
        
        String newId = UUID.randomUUID().toString();
        MDC.put("correlationId", newId);
        return newId;
    }
}