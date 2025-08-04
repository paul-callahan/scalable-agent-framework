package com.pcallahan.agentic.planexecutor.service;

import com.pcallahan.agentic.planexecutor.kafka.PlanExecutionProducer;
import agentic.task.Task.TaskExecution;
import agentic.task.Task.TaskResult;
import agentic.plan.Plan.PlanExecution;
import agentic.plan.Plan.PlanResult;
import agentic.common.Common.ExecutionHeader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.UUID;

/**
 * Service responsible for executing plans based on TaskExecution messages.
 * 
 * This service:
 * - Consumes TaskExecution protobuf messages from Kafka via TaskResultListener
 * - Executes plans based on TaskExecution data
 * - Produces PlanExecution protobuf messages to Kafka via PlanExecutionProducer
 * - Manages plan execution lifecycle and error handling
 */
@Service
public class PlanExecutorService {
    
    private static final Logger logger = LoggerFactory.getLogger(PlanExecutorService.class);
    
    private final PlanExecutionProducer planExecutionProducer;
    private final Map<String, PlanHandler> planHandlers = new ConcurrentHashMap<>();
    private final Map<String, TaskExecution> taskExecutionCache = new ConcurrentHashMap<>();
    
    public PlanExecutorService(PlanExecutionProducer planExecutionProducer) {
        this.planExecutionProducer = planExecutionProducer;
        initializePlanHandlers();
    }
    
    /**
     * Execute plans from a TaskExecution protobuf message
     * 
     * @param taskExecution the TaskExecution protobuf message containing plans to execute
     * @param tenantId the tenant identifier
     * @return true if execution was successful, false otherwise
     */
    public boolean executePlansFromTaskExecution(TaskExecution taskExecution, String tenantId) {
        logger.info("Executing plans from TaskExecution protobuf for tenant: {}", tenantId);
        
        try {
            // Extract TaskResult from TaskExecution
            TaskResult taskResult = taskExecution.getResult();
            
            // Check if there's an error in the task result
            if (!taskResult.getErrorMessage().isEmpty()) {
                logger.error("TaskExecution contains error for tenant {}: {}", tenantId, taskResult.getErrorMessage());
                return false;
            }
            
            logger.debug("TaskExecution protobuf for tenant {}: mime_type={}, size_bytes={}", 
                tenantId, taskResult.getMimeType(), taskResult.getSizeBytes());
            
            // Determine plan type from task result data
            String planType = extractPlanType(taskExecution);
            PlanHandler handler = planHandlers.get(planType);
            
            if (handler == null) {
                logger.error("No handler found for plan type: {} for tenant: {}", planType, tenantId);
                return false;
            }
            
            // Execute the plan using the handler
            PlanExecution planExecution = handler.execute(taskExecution, tenantId);
            if (planExecution == null) {
                logger.error("Plan handler returned null for tenant: {}", tenantId);
                return false;
            }
            
            // Publish the plan execution to Kafka
            planExecutionProducer.publishPlanExecution(tenantId, planExecution)
                .whenComplete((result, throwable) -> {
                    if (throwable != null) {
                        logger.error("Failed to publish PlanExecution for tenant {}: {}", 
                            tenantId, throwable.getMessage());
                    } else {
                        logger.debug("Successfully published PlanExecution for tenant {} to topic {}", 
                            tenantId, result.getRecordMetadata().topic());
                    }
                });
            
            logger.info("Successfully executed plan for tenant: {}", tenantId);
            return true;
            
        } catch (Exception e) {
            logger.error("Error executing plans from TaskExecution protobuf for tenant: {}", tenantId, e);
            return false;
        }
    }
    
    /**
     * Initialize plan handlers for different plan types
     */
    private void initializePlanHandlers() {
        // TODO: Register plan handlers for different plan types
        // planHandlers.put("sequential_plan", new SequentialPlanHandler());
        // planHandlers.put("conditional_plan", new ConditionalPlanHandler());
        // planHandlers.put("parallel_plan", new ParallelPlanHandler());
        
        // For now, add a default handler
        planHandlers.put("default", new DefaultPlanHandler());
    }
    
    /**
     * Cache a TaskExecution for upstream reference
     * 
     * @param taskExecution the TaskExecution to cache
     */
    public void cacheTaskExecution(TaskExecution taskExecution) {
        taskExecutionCache.put(taskExecution.getResult().getId(), taskExecution);
    }
    
    /**
     * Extract plan type from TaskExecution
     */
    private String extractPlanType(TaskExecution taskExecution) {
        // TODO: Implement actual plan type extraction from TaskExecution data
        // For now, return default
        return "default";
    }
    
    /**
     * Interface for plan handlers
     * Updated to take TaskExecution and return PlanExecution
     */
    public interface PlanHandler {
        /**
         * Execute a plan based on TaskExecution
         * 
         * @param taskExecution the TaskExecution that triggered this plan
         * @param tenantId the tenant identifier
         * @return PlanExecution protobuf message
         */
        PlanExecution execute(TaskExecution taskExecution, String tenantId);
    }
    
    /**
     * Default plan handler implementation
     */
    private class DefaultPlanHandler implements PlanHandler {
        @Override
        public PlanExecution execute(TaskExecution taskExecution, String tenantId) {
            // TODO: Implement actual plan execution logic
            // For now, create a simple success response with upstream TaskResults
            
            // Extract TaskResult from TaskExecution
            TaskResult taskResult = taskExecution.getResult();
            
            // Retrieve relevant TaskResults from cache based on execution context
            List<TaskResult> upstreamTaskResults = retrieveRelevantTaskResults(taskExecution, tenantId);
            
            PlanResult planResult = PlanResult.newBuilder()
                .addAllUpstreamTasksResults(upstreamTaskResults)
                .addNextTaskIds("task-1")
                .addNextTaskIds("task-2")
                .setConfidence(0.8f)
                .build();
            
            return PlanExecution.newBuilder()
                .setHeader(ExecutionHeader.newBuilder()
                    .setId(UUID.randomUUID().toString())
                    .setTenantId(tenantId)
                    .setCreatedAt(Instant.now().toString())
                    .build())
                .setResult(planResult)
                .setPlanType("default")
                .setInputTaskId(taskResult.getId())
                .build();
        }
        
        /**
         * Retrieve relevant TaskResults from cache based on execution context
         * 
         * @param currentTaskExecution the current TaskExecution that triggered the plan
         * @param tenantId the tenant identifier
         * @return list of relevant upstream TaskResults
         */
        private List<TaskResult> retrieveRelevantTaskResults(TaskExecution currentTaskExecution, String tenantId) {
            List<TaskResult> relevantResults = new ArrayList<>();
            
            // Extract TaskResult from current TaskExecution
            TaskResult currentTaskResult = currentTaskExecution.getResult();
            
            // Extract execution context from current task result
            // Note: TaskResult doesn't directly contain ExecutionHeader, so we'll use
            // the tenantId and other available fields to determine relevance
            
            for (TaskExecution cachedExecution : taskExecutionCache.values()) {
                TaskResult cachedResult = cachedExecution.getResult();
                if (isRelevantTaskResult(cachedResult, currentTaskResult, tenantId)) {
                    relevantResults.add(cachedResult);
                }
            }
            
            logger.debug("Retrieved {} relevant TaskResults from cache for tenant: {}", 
                relevantResults.size(), tenantId);
            
            return relevantResults;
        }
        
        /**
         * Determine if a cached TaskResult is relevant for the current plan execution
         * 
         * @param cachedResult the cached TaskResult to evaluate
         * @param currentTaskResult the current TaskResult that triggered the plan
         * @param tenantId the tenant identifier
         * @return true if the cached result is relevant, false otherwise
         */
        private boolean isRelevantTaskResult(TaskResult cachedResult, TaskResult currentTaskResult, String tenantId) {
            // Skip the current task result itself
            if (cachedResult.getId().equals(currentTaskResult.getId())) {
                return false;
            }
            
            // Basic relevance criteria:
            // 1. Must not have an error
            if (!cachedResult.getErrorMessage().isEmpty()) {
                return false;
            }
            
            // 2. Must have valid data (either inline or URI)
            if (!cachedResult.hasInlineData() && cachedResult.getUri().isEmpty()) {
                return false;
            }
            
            // 3. Must have a reasonable MIME type (not empty)
            if (cachedResult.getMimeType().isEmpty()) {
                return false;
            }
            
            // 4. Must have reasonable size (not zero)
            if (cachedResult.getSizeBytes() == 0) {
                return false;
            }
            
            // TODO: Add more sophisticated relevance logic based on:
            // - Execution context (graph_id, lifetime_id if available)
            // - Task type relationships
            // - Temporal proximity
            // - Data dependencies
            
            // For now, include all valid cached results as potentially relevant
            // This can be refined based on specific business logic requirements
            return true;
        }
    }
} 