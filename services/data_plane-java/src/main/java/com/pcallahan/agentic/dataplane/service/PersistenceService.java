package com.pcallahan.agentic.dataplane.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.pcallahan.agentic.common.ProtobufUtils;
import com.pcallahan.agentic.dataplane.entity.PlanExecutionEntity;
import com.pcallahan.agentic.dataplane.entity.TaskExecutionEntity;
import com.pcallahan.agentic.dataplane.entity.TaskResultEntity;
import com.pcallahan.agentic.dataplane.repository.PlanExecutionRepository;
import com.pcallahan.agentic.dataplane.repository.TaskExecutionRepository;
import com.pcallahan.agentic.dataplane.repository.TaskResultRepository;
import agentic.plan.Plan.PlanExecution;
import agentic.task.Task.TaskExecution;
import agentic.task.Task.TaskResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Service class that orchestrates the persistence workflow.
 * Coordinates between Kafka consumption and database persistence.
 */
@Service
public class PersistenceService {
    
    private static final Logger logger = LoggerFactory.getLogger(PersistenceService.class);
    
    private final TaskExecutionRepository taskExecutionRepository;
    private final PlanExecutionRepository planExecutionRepository;
    private final TaskResultRepository taskResultRepository;
    private final ObjectMapper objectMapper;
    
    @Autowired
    public PersistenceService(
            TaskExecutionRepository taskExecutionRepository,
            PlanExecutionRepository planExecutionRepository,
            TaskResultRepository taskResultRepository,
            ObjectMapper objectMapper) {
        this.taskExecutionRepository = taskExecutionRepository;
        this.planExecutionRepository = planExecutionRepository;
        this.taskResultRepository = taskResultRepository;
        this.objectMapper = objectMapper;
    }
    
    /**
     * Process a TaskExecution protobuf message and persist it to the database.
     * 
     * @param taskExecution the TaskExecution protobuf message
     * @param tenantId the tenant identifier
     * @return true if processing was successful, false otherwise
     */
    @Transactional
    public boolean processTaskExecution(TaskExecution taskExecution, String tenantId) {
        try {
            logger.debug("Processing TaskExecution {} for tenant {}", taskExecution.getHeader().getId(), tenantId);
            
            // Extract TaskResult and save it separately
            TaskResultEntity savedTaskResult = null;
            if (taskExecution.hasResult()) {
                TaskResult taskResult = taskExecution.getResult();
                TaskResultEntity taskResultEntity = convertToTaskResultEntity(taskResult, tenantId);
                savedTaskResult = taskResultRepository.save(taskResultEntity);
                logger.debug("Saved TaskResult {} to database", savedTaskResult.getId());
            }
            
            // Convert protobuf to JPA entity
            TaskExecutionEntity entity = convertToTaskExecutionEntity(taskExecution, tenantId, savedTaskResult);
            
            // Save to database
            TaskExecutionEntity savedEntity = taskExecutionRepository.save(entity);
            logger.debug("Saved TaskExecution {} to database", savedEntity.getId());
            
            logger.info("Successfully processed TaskExecution {} for tenant {}", taskExecution.getHeader().getId(), tenantId);
            return true;
            
        } catch (Exception e) {
            logger.error("Failed to process TaskExecution {} for tenant {}: {}", 
                taskExecution.getHeader().getId(), tenantId, e.getMessage(), e);
            return false;
        }
    }
    
    /**
     * Process a PlanExecution protobuf message and persist it to the database.
     * 
     * @param planExecution the PlanExecution protobuf message
     * @param tenantId the tenant identifier
     * @return true if processing was successful, false otherwise
     */
    @Transactional
    public boolean processPlanExecution(PlanExecution planExecution, String tenantId) {
        try {
            logger.debug("Processing PlanExecution {} for tenant {}", planExecution.getHeader().getId(), tenantId);
            
            // Convert protobuf to JPA entity
            PlanExecutionEntity entity = convertToPlanExecutionEntity(planExecution, tenantId);
            
            // Save to database
            PlanExecutionEntity savedEntity = planExecutionRepository.save(entity);
            logger.debug("Saved PlanExecution {} to database", savedEntity.getId());
            
            logger.info("Successfully processed PlanExecution {} for tenant {}", planExecution.getHeader().getId(), tenantId);
            return true;
            
        } catch (Exception e) {
            logger.error("Failed to process PlanExecution {} for tenant {}: {}", 
                planExecution.getHeader().getId(), tenantId, e.getMessage(), e);
            return false;
        }
    }
    
    /**
     * Convert TaskExecution protobuf to TaskExecutionEntity.
     * 
     * @param taskExecution the protobuf message
     * @param tenantId the tenant identifier
     * @param savedTaskResult the saved TaskResult entity (can be null)
     * @return the JPA entity
     */
    private TaskExecutionEntity convertToTaskExecutionEntity(TaskExecution taskExecution, String tenantId, TaskResultEntity savedTaskResult) {
        TaskExecutionEntity entity = new TaskExecutionEntity();
        
        // Set basic fields from header
        var header = taskExecution.getHeader();
        entity.setId(header.getId());
        entity.setParentId(header.getParentId());
        entity.setGraphId(header.getGraphId());
        entity.setLifetimeId(header.getLifetimeId());
        entity.setTenantId(tenantId);
        entity.setAttempt(header.getAttempt());
        entity.setIterationIdx(header.getIterationIdx());
        entity.setCreatedAt(Instant.parse(header.getCreatedAt()));
        entity.setStatus(convertStatus(header.getStatus()));
        entity.setEdgeTaken(header.getEdgeTaken());
        
        // Set task-specific fields
        entity.setTaskType(taskExecution.getTaskType());
        
        // Set task result ID using the saved entity's ID
        if (savedTaskResult != null) {
            entity.setTaskResultId(savedTaskResult.getId());
        }
        
        return entity;
    }
    
    /**
     * Convert PlanExecution protobuf to PlanExecutionEntity.
     * 
     * @param planExecution the protobuf message
     * @param tenantId the tenant identifier
     * @return the JPA entity
     */
    private PlanExecutionEntity convertToPlanExecutionEntity(PlanExecution planExecution, String tenantId) {
        PlanExecutionEntity entity = new PlanExecutionEntity();
        
        // Set basic fields from header
        var header = planExecution.getHeader();
        entity.setId(header.getId());
        entity.setParentId(header.getParentId());
        entity.setGraphId(header.getGraphId());
        entity.setLifetimeId(header.getLifetimeId());
        entity.setTenantId(tenantId);
        entity.setAttempt(header.getAttempt());
        entity.setIterationIdx(header.getIterationIdx());
        entity.setCreatedAt(Instant.parse(header.getCreatedAt()));
        entity.setStatus(convertPlanStatus(header.getStatus()));
        entity.setEdgeTaken(header.getEdgeTaken());
        
        // Set plan-specific fields
        entity.setPlanType(planExecution.getPlanType());
        entity.setInputTaskId(planExecution.getInputTaskId());
        
        // Set result fields
        if (planExecution.hasResult()) {
            var result = planExecution.getResult();
            entity.setResultNextTaskIds(result.getNextTaskIdsList());
            entity.setResultMetadata(convertResultMetadata(result.getMetadata()));
            entity.setErrorMessage(result.getErrorMessage());
            entity.setConfidence((double) result.getConfidence());
            
            // Extract upstream TaskResult IDs
            if (!result.getUpstreamTasksResultsList().isEmpty()) {
                var upstreamTaskResultIds = result.getUpstreamTasksResultsList().stream()
                    .map(TaskResult::getId)
                    .toList();
                entity.setUpstreamTaskResultIds(upstreamTaskResultIds);
            }
        }
        
        return entity;
    }
    
    /**
     * Convert protobuf status to JPA enum.
     * 
     * @param status the protobuf status
     * @return the JPA status enum
     */
    private TaskExecutionEntity.ExecutionStatus convertStatus(agentic.common.Common.ExecutionStatus status) {
        return switch (status) {
            case EXECUTION_STATUS_PENDING -> TaskExecutionEntity.ExecutionStatus.EXECUTION_STATUS_PENDING;
            case EXECUTION_STATUS_RUNNING -> TaskExecutionEntity.ExecutionStatus.EXECUTION_STATUS_RUNNING;
            case EXECUTION_STATUS_SUCCEEDED -> TaskExecutionEntity.ExecutionStatus.EXECUTION_STATUS_SUCCEEDED;
            case EXECUTION_STATUS_FAILED -> TaskExecutionEntity.ExecutionStatus.EXECUTION_STATUS_FAILED;
            default -> TaskExecutionEntity.ExecutionStatus.EXECUTION_STATUS_UNSPECIFIED;
        };
    }
    
    /**
     * Convert protobuf status to JPA enum for plan executions.
     * 
     * @param status the protobuf status
     * @return the JPA status enum
     */
    private PlanExecutionEntity.ExecutionStatus convertPlanStatus(agentic.common.Common.ExecutionStatus status) {
        return switch (status) {
            case EXECUTION_STATUS_PENDING -> PlanExecutionEntity.ExecutionStatus.EXECUTION_STATUS_PENDING;
            case EXECUTION_STATUS_RUNNING -> PlanExecutionEntity.ExecutionStatus.EXECUTION_STATUS_RUNNING;
            case EXECUTION_STATUS_SUCCEEDED -> PlanExecutionEntity.ExecutionStatus.EXECUTION_STATUS_SUCCEEDED;
            case EXECUTION_STATUS_FAILED -> PlanExecutionEntity.ExecutionStatus.EXECUTION_STATUS_FAILED;
            default -> PlanExecutionEntity.ExecutionStatus.EXECUTION_STATUS_UNSPECIFIED;
        };
    }
    
    /**
     * Convert TaskResult protobuf to Map.
     * 
     * @param result the TaskResult protobuf
     * @return the result data map
     */
    private Map<String, Object> convertResultData(agentic.task.Task.TaskResult result) {
        Map<String, Object> data = new HashMap<>();
        data.put("mime_type", result.getMimeType());
        data.put("size_bytes", result.getSizeBytes());
        data.put("error_message", result.getErrorMessage());
        
        // Handle data field
        if (result.hasInlineData()) {
            data.put("data_type", "inline");
            data.put("data", result.getInlineData().toString());
        } else if (result.hasUri()) {
            data.put("data_type", "uri");
            data.put("data", result.getUri());
        }
        
        return data;
    }
    
    /**
     * Convert TaskResult protobuf to TaskResultEntity.
     * 
     * @param taskResult the TaskResult protobuf
     * @param tenantId the tenant identifier
     * @return the TaskResultEntity
     */
    private TaskResultEntity convertToTaskResultEntity(TaskResult taskResult, String tenantId) {
        TaskResultEntity entity = new TaskResultEntity();
        
        // Generate ID if not provided
        String taskResultId = taskResult.getId().isEmpty() ? UUID.randomUUID().toString() : taskResult.getId();
        entity.setId(taskResultId);
        entity.setTenantId(tenantId);
        entity.setMimeType(taskResult.getMimeType());
        entity.setSizeBytes(taskResult.getSizeBytes());
        entity.setErrorMessage(taskResult.getErrorMessage());
        entity.setResultData(convertResultData(taskResult));
        
        return entity;
    }
    
    /**
     * Convert PlanResult metadata to Map.
     * 
     * @param metadata the protobuf metadata map
     * @return the metadata map
     */
    private Map<String, Object> convertResultMetadata(java.util.Map<String, String> metadata) {
        return new HashMap<>(metadata);
    }
} 