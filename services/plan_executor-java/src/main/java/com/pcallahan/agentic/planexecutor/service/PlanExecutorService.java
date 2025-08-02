package com.pcallahan.agentic.planexecutor.service;

import com.pcallahan.agentic.planexecutor.kafka.PlanExecutionProducer;
import agentic.task.Task.TaskResult;
import agentic.plan.Plan.PlanExecution;
import agentic.plan.Plan.PlanResult;
import agentic.common.Common.ExecutionHeader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.UUID;

/**
 * Service responsible for executing plans based on TaskResult messages.
 * 
 * This service:
 * - Consumes TaskResult protobuf messages from Kafka via TaskResultListener
 * - Executes plans based on TaskResult data
 * - Produces PlanExecution protobuf messages to Kafka via PlanExecutionProducer
 * - Manages plan execution lifecycle and error handling
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
     * Execute plans from a TaskResult protobuf message
     * 
     * @param taskResult the TaskResult protobuf message containing plans to execute
     * @param tenantId the tenant identifier
     * @return true if execution was successful, false otherwise
     */
    public boolean executePlansFromTaskResult(TaskResult taskResult, String tenantId) {
        logger.info("Executing plans from TaskResult protobuf for tenant: {}", tenantId);
        
        try {
            // Check if there's an error in the task result
            if (!taskResult.getErrorMessage().isEmpty()) {
                logger.error("TaskResult contains error for tenant {}: {}", tenantId, taskResult.getErrorMessage());
                return false;
            }
            
            logger.debug("TaskResult protobuf for tenant {}: mime_type={}, size_bytes={}", 
                tenantId, taskResult.getMimeType(), taskResult.getSizeBytes());
            
            // Determine plan type from task result data
            String planType = extractPlanType(taskResult);
            PlanHandler handler = planHandlers.get(planType);
            
            if (handler == null) {
                logger.error("No handler found for plan type: {} for tenant: {}", planType, tenantId);
                return false;
            }
            
            // Execute the plan using the handler
            PlanExecution planExecution = handler.execute(taskResult, tenantId);
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
            logger.error("Error executing plans from TaskResult protobuf for tenant: {}", tenantId, e);
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
     * Extract plan type from TaskResult
     */
    private String extractPlanType(TaskResult taskResult) {
        // TODO: Implement actual plan type extraction from TaskResult data
        // For now, return default
        return "default";
    }
    
    /**
     * Interface for plan handlers
     * Updated to take TaskResult and return PlanExecution
     */
    public interface PlanHandler {
        /**
         * Execute a plan based on TaskResult
         * 
         * @param taskResult the TaskResult that triggered this plan
         * @param tenantId the tenant identifier
         * @return PlanExecution protobuf message
         */
        PlanExecution execute(TaskResult taskResult, String tenantId);
    }
    
    /**
     * Default plan handler implementation
     */
    private static class DefaultPlanHandler implements PlanHandler {
        @Override
        public PlanExecution execute(TaskResult taskResult, String tenantId) {
            // TODO: Implement actual plan execution logic
            // For now, create a simple success response
            
            PlanResult planResult = PlanResult.newBuilder()
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
                .setInputTaskId("input-task")
                .setParameters("{}")
                .build();
        }
    }
} 