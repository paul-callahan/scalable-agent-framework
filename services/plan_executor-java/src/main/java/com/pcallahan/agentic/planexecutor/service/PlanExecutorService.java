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
 * - Enhances parent relationship population with actual upstream execution data
 */
@Service
public class PlanExecutorService {
    
    private static final Logger logger = LoggerFactory.getLogger(PlanExecutorService.class);
    
    private final PlanExecutionProducer planExecutionProducer;
    private final Map<String, PlanHandler> planHandlers = new ConcurrentHashMap<>();
    
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
     * Default plan handler implementation with enhanced parent relationship population
     */
    private class DefaultPlanHandler implements PlanHandler {
        @Override
        public PlanExecution execute(TaskExecution taskExecution, String tenantId) {
            // TODO: Implement actual plan execution logic
            // For now, create a simple success response with enhanced parent relationships
            
            // Extract TaskResult from TaskExecution
            TaskResult taskResult = taskExecution.getResult();
            
            // Enhanced parent relationship population using actual upstream data
            List<String> parentTaskNames = buildParentTaskNames(taskExecution, tenantId);
            List<TaskResult> upstreamTaskResults = buildUpstreamTaskResults(taskExecution, tenantId);
            
            // Add the current task result to upstream results if it's valid
            if (isValidTaskResult(taskResult)) {
                upstreamTaskResults.add(taskResult);
            }
            
            logger.debug("Plan execution will have {} parent task names: {}", 
                parentTaskNames.size(), parentTaskNames);
            logger.debug("Plan execution will have {} upstream task results", 
                upstreamTaskResults.size());
            
            PlanResult planResult = PlanResult.newBuilder()
                .addAllUpstreamTasksResults(upstreamTaskResults)
                .addNextTaskIds("task-1")
                .addNextTaskIds("task-2")
                .setConfidence(0.8f)
                .build();
            
            return PlanExecution.newBuilder()
                .setHeader(ExecutionHeader.newBuilder()
                    .setExecId(UUID.randomUUID().toString())
                    .setName("default_plan")
                    .setTenantId(tenantId)
                    .setCreatedAt(Instant.now().toString())
                    .build())
                .setResult(planResult)
                .setPlanType("default")
                .setInputTaskId(taskResult.getId())
                .addAllParentTaskNames(parentTaskNames)
                .build();
        }
        
        /**
         * Build parent task names list based on the current task execution context
         * 
         * @param currentTaskExecution the current TaskExecution that triggered the plan
         * @param tenantId the tenant identifier
         * @return list of parent task names from the current execution context
         */
        private List<String> buildParentTaskNames(TaskExecution currentTaskExecution, String tenantId) {
            List<String> parentTaskNames = new ArrayList<>();
            
            // Add the current task name as the primary parent
            String currentTaskName = currentTaskExecution.getHeader().getName();
            if (currentTaskName != null && !currentTaskName.isEmpty()) {
                parentTaskNames.add(currentTaskName);
            }
            
            // TODO: In a real implementation, this would look up the graph definition
            // to find the actual parent task names based on the graph structure.
            // For now, we only include the current task name as it's the immediate parent
            // that triggered this plan execution.
            
            logger.debug("Built parent task names for tenant {}: {}", tenantId, parentTaskNames);
            
            return parentTaskNames;
        }
        
        /**
         * Build upstream task results based on the current task execution context
         * 
         * @param currentTaskExecution the current TaskExecution that triggered the plan
         * @param tenantId the tenant identifier
         * @return list of relevant upstream TaskResults
         */
        private List<TaskResult> buildUpstreamTaskResults(TaskExecution currentTaskExecution, String tenantId) {
            List<TaskResult> upstreamResults = new ArrayList<>();
            
            // Extract TaskResult from current TaskExecution
            TaskResult currentTaskResult = currentTaskExecution.getResult();
            
            // TODO: In a real implementation, this would:
            // 1. Look up the graph definition to understand the execution flow
            // 2. Query the data plane for actual upstream task results based on graph_id/lifetime_id
            // 3. Include only the relevant upstream results based on the graph structure
            
            // For now, we only include the current task result as the primary upstream result
            // since it's the immediate trigger for this plan execution
            if (isValidTaskResult(currentTaskResult)) {
                upstreamResults.add(currentTaskResult);
            }
            
            logger.debug("Built {} upstream task results for tenant {}", upstreamResults.size(), tenantId);
            
            return upstreamResults;
        }
        
        /**
         * Check if a TaskResult is valid for inclusion in upstream results
         * 
         * @param taskResult the TaskResult to validate
         * @return true if the result is valid, false otherwise
         */
        private boolean isValidTaskResult(TaskResult taskResult) {
            return taskResult != null && 
                   taskResult.getErrorMessage().isEmpty() &&
                   !taskResult.getMimeType().isEmpty() &&
                   taskResult.getSizeBytes() > 0;
        }
    }
} 