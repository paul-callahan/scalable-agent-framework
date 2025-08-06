package com.pcallahan.agentic.controlplane.service;

import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.controlplane.kafka.ExecutorProducer;
import io.arl.proto.model.Task.TaskExecution;
import io.arl.proto.model.Plan.PlanExecution;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * Service for routing execution messages to appropriate executors.
 * 
 * This service implements the corrected routing logic:
 * - TaskExecution (full execution messages) goes to PlanExecutor to decide next steps
 * - PlanExecution (full execution messages) goes to TaskExecutor to execute those tasks
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
                // Route full TaskExecution to PlanExecutor
                executorProducer.publishTaskExecution(tenantId, taskExecution);
                
                logger.info("Task execution approved and routed to PlanExecutor for tenant: {}", tenantId);
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
                // Route full PlanExecution to TaskExecutor
                executorProducer.publishPlanExecution(tenantId, planExecution);
                
                logger.info("Plan execution approved and routed to TaskExecutor for tenant: {}", tenantId);
            } else {
                logger.warn("Plan execution rejected by guardrails for tenant: {}", tenantId);
                // Could implement rejection handling here
            }
            
            // TODO: Future routing logic may use the new parent_task_exec_ids field
            // for more sophisticated routing decisions based on parent execution relationships
            
        } catch (Exception e) {
            logger.error("Error routing plan execution for tenant {}: {}", tenantId, e.getMessage(), e);
        }
    }
} 