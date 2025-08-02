package com.pcallahan.agentic.controlplane.service;

import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.controlplane.kafka.ExecutorProducer;
import agentic.task.Task.TaskExecution;
import agentic.task.Task.TaskResult;
import agentic.plan.Plan.PlanExecution;
import agentic.plan.Plan.PlanResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * Service for routing execution messages to appropriate executors.
 * 
 * This service implements the corrected routing logic:
 * - TaskResult (output from tasks) goes to PlanExecutor to decide next steps
 * - PlanResult (decisions about next tasks) goes to TaskExecutor to execute those tasks
 */
@Service
public class ExecutionRouter {
    
    private static final Logger logger = LoggerFactory.getLogger(ExecutionRouter.class);
    
    private final ExecutorProducer executorProducer;
    private final GuardrailEngine guardrailEngine;
    
    @Autowired
    public ExecutionRouter(ExecutorProducer executorProducer, GuardrailEngine guardrailEngine) {
        this.executorProducer = executorProducer;
        this.guardrailEngine = guardrailEngine;
    }
    
    /**
     * Route task execution protobuf message to appropriate handler.
     * 
     * @param taskExecution the TaskExecution protobuf message
     * @param tenantId the tenant identifier
     */
    public void routeTaskExecution(TaskExecution taskExecution, String tenantId) {
        try {
            logger.debug("Routing task execution for tenant: {}", tenantId);
            
            // Evaluate guardrails for task execution
            boolean approved = guardrailEngine.evaluateTaskExecution(taskExecution, tenantId);
            
            if (approved) {
                // Extract TaskResult from task execution and route to PlanExecutor
                TaskResult taskResult = extractTaskResult(taskExecution);
                executorProducer.publishTaskResult(tenantId, taskResult);
                
                logger.info("Task execution approved and TaskResult routed to PlanExecutor for tenant: {}", tenantId);
            } else {
                logger.warn("Task execution rejected by guardrails for tenant: {}", tenantId);
                // Could implement rejection handling here
            }
            
        } catch (Exception e) {
            logger.error("Error routing task execution for tenant {}: {}", tenantId, e.getMessage(), e);
        }
    }
    
    /**
     * Route plan execution protobuf message to appropriate handler.
     * 
     * @param planExecution the PlanExecution protobuf message
     * @param tenantId the tenant identifier
     */
    public void routePlanExecution(PlanExecution planExecution, String tenantId) {
        try {
            logger.debug("Routing plan execution for tenant: {}", tenantId);
            
            // Evaluate guardrails for plan execution
            boolean approved = guardrailEngine.evaluatePlanExecution(planExecution, tenantId);
            
            if (approved) {
                // Extract PlanResult from plan execution and route to TaskExecutor
                PlanResult planResult = extractPlanResult(planExecution);
                executorProducer.publishPlanResult(tenantId, planResult);
                
                logger.info("Plan execution approved and PlanResult routed to TaskExecutor for tenant: {}", tenantId);
            } else {
                logger.warn("Plan execution rejected by guardrails for tenant: {}", tenantId);
                // Could implement rejection handling here
            }
            
        } catch (Exception e) {
            logger.error("Error routing plan execution for tenant {}: {}", tenantId, e.getMessage(), e);
        }
    }
    
    /**
     * Extract TaskResult from TaskExecution protobuf message.
     * 
     * @param taskExecution the TaskExecution protobuf message
     * @return TaskResult protobuf message
     */
    private TaskResult extractTaskResult(TaskExecution taskExecution) {
        // Extract TaskResult from TaskExecution.result field
        return taskExecution.getResult();
    }
    
    /**
     * Extract PlanResult from PlanExecution protobuf message.
     * 
     * @param planExecution the PlanExecution protobuf message
     * @return PlanResult protobuf message
     */
    private PlanResult extractPlanResult(PlanExecution planExecution) {
        // Extract PlanResult from PlanExecution.result field
        return planExecution.getResult();
    }
} 