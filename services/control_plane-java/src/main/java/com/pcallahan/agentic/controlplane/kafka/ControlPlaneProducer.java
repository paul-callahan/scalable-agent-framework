package com.pcallahan.agentic.controlplane.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.pcallahan.agentic.common.TopicNames;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * Kafka producer for the Control Plane service.
 * 
 * This producer:
 * - Sends approved task executions to task executor queue
 * - Sends approved plan executions to plan executor queue
 * - Handles message serialization and error handling
 */
@Component
public class ControlPlaneProducer {
    
    private static final Logger logger = LoggerFactory.getLogger(ControlPlaneProducer.class);
    
    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final ObjectMapper objectMapper;
    
    public ControlPlaneProducer(KafkaTemplate<String, Object> kafkaTemplate, ObjectMapper objectMapper) {
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = objectMapper;
    }
    
    /**
     * Send task execution to task executor queue.
     * 
     * @param taskExecution the task execution data
     * @param tenantId the tenant identifier
     */
    public void sendTaskExecution(Map<String, Object> taskExecution, String tenantId) {
        try {
            logger.debug("Sending task execution to executor queue for tenant {}: {}", tenantId, taskExecution);
            kafkaTemplate.send(TopicNames.taskExecutions(tenantId), taskExecution);
            logger.info("Task execution sent to executor queue for tenant: {}", tenantId);
        } catch (Exception e) {
            logger.error("Failed to send task execution to executor queue for tenant: {}", tenantId, e);
        }
    }
    
    /**
     * Send plan execution to plan executor queue.
     * 
     * @param planExecution the plan execution data
     * @param tenantId the tenant identifier
     */
    public void sendPlanExecution(Map<String, Object> planExecution, String tenantId) {
        try {
            logger.debug("Sending plan execution to executor queue for tenant {}: {}", tenantId, planExecution);
            kafkaTemplate.send(TopicNames.planExecutions(tenantId), planExecution);
            logger.info("Plan execution sent to executor queue for tenant: {}", tenantId);
        } catch (Exception e) {
            logger.error("Failed to send plan execution to executor queue for tenant: {}", tenantId, e);
        }
    }
    
    /**
     * Send task execution rejection.
     * 
     * @param taskExecution the task execution data
     * @param reason the rejection reason
     * @param tenantId the tenant identifier
     */
    public void sendTaskExecutionRejection(Map<String, Object> taskExecution, String reason, String tenantId) {
        try {
            Map<String, Object> rejection = Map.of(
                "task_execution", taskExecution,
                "rejected", true,
                "reason", reason,
                "timestamp", System.currentTimeMillis()
            );
            
            logger.debug("Sending task execution rejection for tenant {}: {}", tenantId, rejection);
            kafkaTemplate.send(TopicNames.taskResults(tenantId), rejection);
            logger.info("Task execution rejection sent for tenant: {}", tenantId);
        } catch (Exception e) {
            logger.error("Failed to send task execution rejection for tenant: {}", tenantId, e);
        }
    }
    
    /**
     * Send plan execution rejection.
     * 
     * @param planExecution the plan execution data
     * @param reason the rejection reason
     * @param tenantId the tenant identifier
     */
    public void sendPlanExecutionRejection(Map<String, Object> planExecution, String reason, String tenantId) {
        try {
            Map<String, Object> rejection = Map.of(
                "plan_execution", planExecution,
                "rejected", true,
                "reason", reason,
                "timestamp", System.currentTimeMillis()
            );
            
            logger.debug("Sending plan execution rejection for tenant {}: {}", tenantId, rejection);
            kafkaTemplate.send(TopicNames.planResults(tenantId), rejection);
            logger.info("Plan execution rejection sent for tenant: {}", tenantId);
        } catch (Exception e) {
            logger.error("Failed to send plan execution rejection for tenant: {}", tenantId, e);
        }
    }
} 