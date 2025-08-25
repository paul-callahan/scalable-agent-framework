package com.pcallahan.agentic.graphcomposer.service;

import com.pcallahan.agentic.graph.entity.AgentGraphEntity;
import com.pcallahan.agentic.graph.entity.PlanEntity;
import com.pcallahan.agentic.graph.entity.TaskEntity;
import com.pcallahan.agentic.graph.repository.AgentGraphRepository;
import com.pcallahan.agentic.graph.repository.PlanRepository;
import com.pcallahan.agentic.graph.repository.TaskRepository;
import com.pcallahan.agentic.graphcomposer.dto.*;
import com.pcallahan.agentic.graphcomposer.exception.GraphValidationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Implementation of GraphService for Agent Graph management operations.
 * Provides business logic for graph CRUD operations with tenant isolation.
 */
@Service
@Transactional
public class GraphServiceImpl implements GraphService {

    private static final Logger logger = LoggerFactory.getLogger(GraphServiceImpl.class);

    private final AgentGraphRepository agentGraphRepository;
    private final PlanRepository planRepository;
    private final TaskRepository taskRepository;
    private final FileService fileService;
    private final ValidationService validationService;

    @Autowired
    public GraphServiceImpl(AgentGraphRepository agentGraphRepository,
                           PlanRepository planRepository,
                           TaskRepository taskRepository,
                           FileService fileService,
                           ValidationService validationService) {
        this.agentGraphRepository = agentGraphRepository;
        this.planRepository = planRepository;
        this.taskRepository = taskRepository;
        this.fileService = fileService;
        this.validationService = validationService;
    }

    @Override
    @Transactional(readOnly = true)
    public List<AgentGraphSummary> listGraphs(String tenantId) {
        logger.info("Listing graphs for tenant: {}", tenantId);
        
        // Use optimized query that doesn't fetch relationships for listing
        List<AgentGraphEntity> graphs = agentGraphRepository.findByTenantIdOptimized(tenantId);
        
        return graphs.stream()
                .map(this::convertToSummary)
                .collect(Collectors.toList());
    }

    @Override
    @Transactional(readOnly = true)
    public AgentGraphDto getGraph(String graphId, String tenantId) {
        logger.info("Getting graph {} for tenant: {}", graphId, tenantId);
        
        // Use optimized query with fetch joins to avoid N+1 problems
        AgentGraphEntity graph = agentGraphRepository.findByIdAndTenantIdWithAllRelations(graphId, tenantId)
                .orElseThrow(() -> new GraphNotFoundException("Graph not found: " + graphId));
        
        return convertToDtoOptimized(graph);
    }

    @Override
    public AgentGraphDto createGraph(CreateGraphRequest request) {
        logger.info("Creating new graph '{}' for tenant: {}", request.getName(), request.getTenantId());
        
        AgentGraphEntity graph = new AgentGraphEntity();
        graph.setId(UUID.randomUUID().toString());
        graph.setName(request.getName());
        graph.setTenantId(request.getTenantId());
        graph.setStatus(com.pcallahan.agentic.graph.entity.GraphStatus.NEW);
        graph.setCreatedAt(LocalDateTime.now());
        graph.setUpdatedAt(LocalDateTime.now());
        
        AgentGraphEntity savedGraph = agentGraphRepository.save(graph);
        
        logger.info("Created graph with ID: {}", savedGraph.getId());
        return convertToDto(savedGraph);
    }

    @Override
    public AgentGraphDto updateGraph(String graphId, AgentGraphDto graphDto) {
        logger.info("Updating graph {} for tenant: {}", graphId, graphDto.getTenantId());
        
        AgentGraphEntity existingGraph = agentGraphRepository.findByIdAndTenantId(graphId, graphDto.getTenantId())
                .orElseThrow(() -> new GraphNotFoundException("Graph not found: " + graphId));
        
        // Validate the graph before updating
        ValidationResult validation = validationService.validateGraph(graphDto);
        if (!validation.isValid()) {
            throw new GraphValidationException("Graph validation failed", validation.getErrors(), validation.getWarnings());
        }
        
        // Update basic properties
        existingGraph.setName(graphDto.getName());
        existingGraph.setUpdatedAt(LocalDateTime.now());
        
        // Update status if provided
        if (graphDto.getStatus() != null) {
            existingGraph.setStatus(convertToEntityStatus(graphDto.getStatus()));
        }
        
        // Save graph first to ensure it exists
        AgentGraphEntity savedGraph = agentGraphRepository.save(existingGraph);
        
        // Update plans and their files
        updatePlansAndFiles(savedGraph, graphDto.getPlans());
        
        // Update tasks and their files  
        updateTasksAndFiles(savedGraph, graphDto.getTasks());
        
        logger.info("Updated graph: {}", savedGraph.getId());
        
        // Return the updated graph DTO
        AgentGraphDto updatedDto = new AgentGraphDto();
        updatedDto.setId(savedGraph.getId());
        updatedDto.setName(savedGraph.getName());
        updatedDto.setTenantId(savedGraph.getTenantId());
        updatedDto.setStatus(convertToDtoStatus(savedGraph.getStatus()));
        updatedDto.setPlans(graphDto.getPlans());
        updatedDto.setTasks(graphDto.getTasks());
        updatedDto.setCreatedAt(savedGraph.getCreatedAt());
        updatedDto.setUpdatedAt(savedGraph.getUpdatedAt());
        
        return updatedDto;
    }

    @Override
    public void deleteGraph(String graphId, String tenantId) {
        logger.info("Deleting graph {} for tenant: {}", graphId, tenantId);
        
        AgentGraphEntity graph = agentGraphRepository.findByIdAndTenantId(graphId, tenantId)
                .orElseThrow(() -> new GraphNotFoundException("Graph not found: " + graphId));
        
        agentGraphRepository.delete(graph);
        
        logger.info("Deleted graph: {}", graphId);
    }



    @Override
    public ExecutionResponse submitForExecution(String graphId, String tenantId) {
        logger.info("Submitting graph {} for execution for tenant: {}", graphId, tenantId);
        
        AgentGraphEntity graph = agentGraphRepository.findByIdAndTenantId(graphId, tenantId)
                .orElseThrow(() -> new GraphNotFoundException("Graph not found: " + graphId));
        
        // Validate graph before execution
        AgentGraphDto graphDto = convertToDto(graph);
        ValidationResult validation = validationService.validateGraph(graphDto);
        if (!validation.isValid()) {
            throw new GraphValidationException("Cannot execute invalid graph", validation.getErrors(), validation.getWarnings());
        }
        
        // Update status to running
        graph.setStatus(com.pcallahan.agentic.graph.entity.GraphStatus.RUNNING);
        graph.setUpdatedAt(LocalDateTime.now());
        agentGraphRepository.save(graph);
        
        // Create execution response (placeholder implementation)
        ExecutionResponse response = new ExecutionResponse();
        response.setExecutionId(UUID.randomUUID().toString());
        response.setStatus("SUBMITTED");
        response.setMessage("Graph submitted for execution");
        
        logger.info("Graph {} submitted for execution with ID: {}", graphId, response.getExecutionId());
        return response;
    }

    @Override
    public void updateGraphStatus(String graphId, GraphStatusUpdate statusUpdate) {
        logger.info("Updating status for graph {} to: {}", graphId, statusUpdate.getStatus());
        
        AgentGraphEntity graph = agentGraphRepository.findById(graphId)
                .orElseThrow(() -> new GraphNotFoundException("Graph not found: " + graphId));
        
        graph.setStatus(convertToEntityStatus(statusUpdate.getStatus()));
        graph.setUpdatedAt(LocalDateTime.now());
        agentGraphRepository.save(graph);
        
        logger.info("Updated graph {} status to: {}", graphId, statusUpdate.getStatus());
    }

    private AgentGraphSummary convertToSummary(AgentGraphEntity entity) {
        return new AgentGraphSummary(
                entity.getId(),
                entity.getName(),
                convertToDtoStatus(entity.getStatus()),
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }

    private AgentGraphDto convertToDto(AgentGraphEntity entity) {
        // Get plans and tasks for this graph using optimized queries
        List<PlanEntity> plans = planRepository.findByAgentGraphIdWithFiles(entity.getId());
        List<TaskEntity> tasks = taskRepository.findByAgentGraphIdWithFiles(entity.getId());
        
        List<PlanDto> planDtos = plans.stream()
                .map(this::convertPlanToDto)
                .collect(Collectors.toList());
        
        List<TaskDto> taskDtos = tasks.stream()
                .map(this::convertTaskToDto)
                .collect(Collectors.toList());
        
        return new AgentGraphDto(
                entity.getId(),
                entity.getName(),
                entity.getTenantId(),
                convertToDtoStatus(entity.getStatus()),
                planDtos,
                taskDtos,
                null, // planToTasks mapping would be computed from relationships
                null, // taskToPlan mapping would be computed from relationships
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }

    /**
     * Optimized conversion when entity already has all relationships loaded.
     */
    private AgentGraphDto convertToDtoOptimized(AgentGraphEntity entity) {
        List<PlanDto> planDtos = entity.getPlans().stream()
                .map(this::convertPlanToDtoOptimized)
                .collect(Collectors.toList());
        
        List<TaskDto> taskDtos = entity.getTasks().stream()
                .map(this::convertTaskToDtoOptimized)
                .collect(Collectors.toList());
        
        return new AgentGraphDto(
                entity.getId(),
                entity.getName(),
                entity.getTenantId(),
                convertToDtoStatus(entity.getStatus()),
                planDtos,
                taskDtos,
                null, // planToTasks mapping would be computed from relationships
                null, // taskToPlan mapping would be computed from relationships
                entity.getCreatedAt(),
                entity.getUpdatedAt()
        );
    }

    private PlanDto convertPlanToDto(PlanEntity entity) {
        List<ExecutorFileDto> files = fileService.getPlanFiles(entity.getId());
        
        return new PlanDto(
                entity.getName(),
                entity.getLabel(),
                null, // upstreamTaskIds would be computed from relationships
                files
        );
    }

    private TaskDto convertTaskToDto(TaskEntity entity) {
        List<ExecutorFileDto> files = fileService.getTaskFiles(entity.getId());
        
        return new TaskDto(
                entity.getName(),
                entity.getLabel(),
                null, // upstreamPlanId would be computed from relationships
                files
        );
    }

    /**
     * Optimized conversion when files are already loaded in the entity.
     */
    private PlanDto convertPlanToDtoOptimized(PlanEntity entity) {
        List<ExecutorFileDto> files = entity.getFiles().stream()
                .map(fileService::convertToDto)
                .collect(Collectors.toList());
        
        return new PlanDto(
                entity.getName(),
                entity.getLabel(),
                null, // upstreamTaskIds would be computed from relationships
                files
        );
    }

    /**
     * Optimized conversion when files are already loaded in the entity.
     */
    private TaskDto convertTaskToDtoOptimized(TaskEntity entity) {
        List<ExecutorFileDto> files = entity.getFiles().stream()
                .map(fileService::convertToDto)
                .collect(Collectors.toList());
        
        return new TaskDto(
                entity.getName(),
                entity.getLabel(),
                null, // upstreamPlanId would be computed from relationships
                files
        );
    }

    private GraphStatus convertToDtoStatus(com.pcallahan.agentic.graph.entity.GraphStatus entityStatus) {
        return switch (entityStatus) {
            case NEW -> GraphStatus.NEW;
            case RUNNING -> GraphStatus.RUNNING;
            case STOPPED -> GraphStatus.STOPPED;
            case ERROR -> GraphStatus.ERROR;
        };
    }

    private com.pcallahan.agentic.graph.entity.GraphStatus convertToEntityStatus(GraphStatus dtoStatus) {
        return switch (dtoStatus) {
            case NEW -> com.pcallahan.agentic.graph.entity.GraphStatus.NEW;
            case RUNNING -> com.pcallahan.agentic.graph.entity.GraphStatus.RUNNING;
            case STOPPED -> com.pcallahan.agentic.graph.entity.GraphStatus.STOPPED;
            case ERROR -> com.pcallahan.agentic.graph.entity.GraphStatus.ERROR;
        };
    }
    
    /**
     * Update plans and their associated files for a graph.
     * This method replaces all existing plans with the provided ones.
     */
    private void updatePlansAndFiles(AgentGraphEntity graph, List<PlanDto> planDtos) {
        if (planDtos == null) {
            return;
        }
        
        // Delete existing plans (cascade will handle files)
        planRepository.deleteByAgentGraphId(graph.getId());
        
        // Create new plans with files
        for (PlanDto planDto : planDtos) {
            PlanEntity planEntity = new PlanEntity();
            planEntity.setId(UUID.randomUUID().toString());
            planEntity.setName(planDto.getName());
            planEntity.setLabel(planDto.getLabel());
            planEntity.setAgentGraph(graph);
            
            // Save plan first
            PlanEntity savedPlan = planRepository.save(planEntity);
            
            // Create files for this plan
            createFilesForPlan(savedPlan, planDto.getFiles());
        }
    }
    
    /**
     * Update tasks and their associated files for a graph.
     * This method replaces all existing tasks with the provided ones.
     */
    private void updateTasksAndFiles(AgentGraphEntity graph, List<TaskDto> taskDtos) {
        if (taskDtos == null) {
            return;
        }
        
        // Delete existing tasks (cascade will handle files)
        taskRepository.deleteByAgentGraphId(graph.getId());
        
        // Create new tasks with files
        for (TaskDto taskDto : taskDtos) {
            TaskEntity taskEntity = new TaskEntity();
            taskEntity.setId(UUID.randomUUID().toString());
            taskEntity.setName(taskDto.getName());
            taskEntity.setLabel(taskDto.getLabel());
            taskEntity.setAgentGraph(graph);
            
            // Save task first
            TaskEntity savedTask = taskRepository.save(taskEntity);
            
            // Create files for this task
            createFilesForTask(savedTask, taskDto.getFiles());
        }
    }
    
    /**
     * Create files for a plan entity.
     */
    private void createFilesForPlan(PlanEntity plan, List<ExecutorFileDto> fileDtos) {
        if (fileDtos == null || fileDtos.isEmpty()) {
            return;
        }
        
        for (ExecutorFileDto fileDto : fileDtos) {
            fileService.updatePlanFile(plan.getId(), fileDto.getName(), fileDto.getContents());
        }
    }
    
    /**
     * Create files for a task entity.
     */
    private void createFilesForTask(TaskEntity task, List<ExecutorFileDto> fileDtos) {
        if (fileDtos == null || fileDtos.isEmpty()) {
            return;
        }
        
        for (ExecutorFileDto fileDto : fileDtos) {
            fileService.updateTaskFile(task.getId(), fileDto.getName(), fileDto.getContents());
        }
    }
}