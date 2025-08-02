package com.pcallahan.agentic.taskexecutor.service;

import com.pcallahan.agentic.taskexecutor.kafka.TaskExecutionProducer;
import agentic.plan.Plan.PlanResult;
import agentic.task.Task.TaskExecution;
import agentic.task.Task.TaskResult;
import agentic.common.Common.ExecutionHeader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.UUID;

/**
 * Service responsible for executing tasks based on PlanResult messages.
 * 
 * This service:
 * - Consumes PlanResult protobuf messages from Kafka via PlanResultListener
 * - Executes tasks based on PlanResult.nextTaskIds
 * - Produces TaskExecution protobuf messages to Kafka via TaskExecutionProducer
 * - Manages task execution lifecycle and error handling
 */
@Service
public class TaskExecutorService {
    
    private static final Logger logger = LoggerFactory.getLogger(TaskExecutorService.class);
    
    private final TaskExecutionProducer taskExecutionProducer;
    private final Map<String, TaskHandler> taskHandlers = new ConcurrentHashMap<>();
    
    public TaskExecutorService(TaskExecutionProducer taskExecutionProducer) {
        this.taskExecutionProducer = taskExecutionProducer;
        initializeTaskHandlers();
    }
    
    /**
     * Execute tasks from a PlanResult protobuf message
     * 
     * @param planResult the PlanResult protobuf message containing tasks to execute
     * @param tenantId the tenant identifier
     * @return true if execution was successful, false otherwise
     */
    public boolean executeTasksFromPlan(PlanResult planResult, String tenantId) {
        logger.info("Executing tasks from PlanResult protobuf for tenant: {}", tenantId);
        
        try {
            // Check if there's an error in the plan result
            if (!planResult.getErrorMessage().isEmpty()) {
                logger.error("PlanResult contains error for tenant {}: {}", tenantId, planResult.getErrorMessage());
                return false;
            }
            
            // Get the list of task IDs to execute
            var nextTaskIds = planResult.getNextTaskIdsList();
            if (nextTaskIds.isEmpty()) {
                logger.info("No tasks to execute from PlanResult for tenant: {}", tenantId);
                return true;
            }
            
            logger.debug("PlanResult protobuf for tenant {}: next_task_ids={}, confidence={}", 
                tenantId, nextTaskIds, planResult.getConfidence());
            
            // Execute each task in the plan
            boolean allTasksSuccessful = true;
            for (String taskId : nextTaskIds) {
                try {
                    TaskExecution taskExecution = executeTask(taskId, planResult, tenantId);
                    if (taskExecution != null) {
                        // Publish the task execution to Kafka
                        taskExecutionProducer.publishTaskExecution(tenantId, taskExecution)
                            .whenComplete((result, throwable) -> {
                                if (throwable != null) {
                                    logger.error("Failed to publish TaskExecution for tenant {} task {}: {}", 
                                        tenantId, taskId, throwable.getMessage());
                                } else {
                                    logger.debug("Successfully published TaskExecution for tenant {} task {} to topic {}", 
                                        tenantId, taskId, result.getRecordMetadata().topic());
                                }
                            });
                        
                        logger.info("Successfully executed task {} for tenant: {}", taskId, tenantId);
                    } else {
                        logger.error("Failed to execute task {} for tenant: {}", taskId, tenantId);
                        allTasksSuccessful = false;
                    }
                } catch (Exception e) {
                    logger.error("Error executing task {} for tenant: {}", taskId, tenantId, e);
                    allTasksSuccessful = false;
                }
            }
            
            return allTasksSuccessful;
            
        } catch (Exception e) {
            logger.error("Error executing tasks from PlanResult protobuf for tenant: {}", tenantId, e);
            return false;
        }
    }
    
    /**
     * Execute a single task based on task ID and plan result
     * 
     * @param taskId the task identifier
     * @param planResult the PlanResult that triggered this task
     * @param tenantId the tenant identifier
     * @return TaskExecution protobuf message, or null if execution failed
     */
    private TaskExecution executeTask(String taskId, PlanResult planResult, String tenantId) {
        try {
            // Determine task type from task ID or use default
            String taskType = extractTaskType(taskId);
            TaskHandler handler = taskHandlers.get(taskType);
            
            if (handler == null) {
                logger.error("No handler found for task type: {} for tenant: {}", taskType, tenantId);
                return null;
            }
            
            // Execute the task using the handler
            TaskExecution taskExecution = handler.execute(planResult, tenantId);
            if (taskExecution == null) {
                logger.error("Task handler returned null for task {} tenant: {}", taskId, tenantId);
                return null;
            }
            
            return taskExecution;
            
        } catch (Exception e) {
            logger.error("Error executing task {} for tenant: {}", taskId, tenantId, e);
            return null;
        }
    }
    
    /**
     * Initialize task handlers for different task types
     */
    private void initializeTaskHandlers() {
        // TODO: Register task handlers for different task types
        // taskHandlers.put("text_generation", new TextGenerationHandler());
        // taskHandlers.put("code_execution", new CodeExecutionHandler());
        // taskHandlers.put("data_processing", new DataProcessingHandler());
        
        // For now, add a default handler
        taskHandlers.put("default", new DefaultTaskHandler());
    }
    
    /**
     * Extract task type from task ID
     */
    private String extractTaskType(String taskId) {
        // TODO: Implement actual task type extraction from task ID
        // For now, return default
        return "default";
    }
    
    /**
     * Interface for task handlers
     * Updated to take PlanResult and return TaskExecution
     */
    public interface TaskHandler {
        /**
         * Execute a task based on PlanResult
         * 
         * @param planResult the PlanResult that triggered this task
         * @param tenantId the tenant identifier
         * @return TaskExecution protobuf message
         */
        TaskExecution execute(PlanResult planResult, String tenantId);
    }
    
    /**
     * Default task handler implementation
     */
    private static class DefaultTaskHandler implements TaskHandler {
        @Override
        public TaskExecution execute(PlanResult planResult, String tenantId) {
            // TODO: Implement actual task execution logic
            // For now, create a simple success response
            
            TaskResult taskResult = TaskResult.newBuilder()
                .setMimeType("application/json")
                .setSizeBytes(0)
                .build();
            
            return TaskExecution.newBuilder()
                .setHeader(ExecutionHeader.newBuilder()
                    .setId(UUID.randomUUID().toString())
                    .setTenantId(tenantId)
                    .setCreatedAt(Instant.now().toString())
                    .build())
                .setResult(taskResult)
                .setTaskType("default")
                .setParameters("{}")
                .build();
        }
    }
} 