package com.pcallahan.agentic.controlplane.kafka;

import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.common.ProtobufUtils;
import io.arl.proto.model.Task.TaskExecution;
import io.arl.proto.model.Plan.PlanExecution;
import io.arl.proto.model.Plan.PlanInput;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;

/**
 * Kafka producer for the Control Plane service.
 * 
 * This producer correctly routes protobuf messages:
 * - PlanInput messages to plan-inputs-{tenantId} topics (for PlanExecutor to consume)
 * - PlanExecution messages to controlled-plan-executions-{tenantId} topics (for TaskExecutor to consume)
 * - Enhanced with proper parent relationship handling and logging
 */
@Component
public class ExecutorProducer {
    
    private static final Logger logger = LoggerFactory.getLogger(ExecutorProducer.class);
    
    private final KafkaTemplate<String, byte[]> kafkaTemplate;
    
    @Autowired
    public ExecutorProducer(KafkaTemplate<String, byte[]> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }
    
    /**
     * Publish PlanInput protobuf to plan-inputs topic for PlanExecutor to consume.
     * 
     * @param tenantId the tenant identifier
     * @param planInput the PlanInput protobuf message
     * @return CompletableFuture for the send result
     */
    public CompletableFuture<SendResult<String, byte[]>> publishPlanInput(String tenantId, PlanInput planInput) {
        try {
            String topic = TopicNames.planInputs(tenantId);
            
            byte[] message = ProtobufUtils.serializePlanInput(planInput);
            if (message == null) {
                throw new RuntimeException("Failed to serialize PlanInput");
            }
            
            String messageKey = planInput.getPlanName();
            
            logger.debug("Publishing PlanInput protobuf to topic {}: {}", topic, messageKey);
            
            ProducerRecord<String, byte[]> record = new ProducerRecord<>(topic, messageKey, message);
            return kafkaTemplate.send(record);
            
        } catch (Exception e) {
            logger.error("Failed to publish PlanInput protobuf for tenant {}: {}", tenantId, e.getMessage(), e);
            CompletableFuture<SendResult<String, byte[]>> future = new CompletableFuture<>();
            future.completeExceptionally(e);
            return future;
        }
    }
    
    /**
     * Publish PlanExecution protobuf to controlled-plan-executions topic for TaskExecutor to consume.
     * 
     * @param tenantId the tenant identifier
     * @param planExecution the PlanExecution protobuf message
     * @return CompletableFuture for the send result
     */
    public CompletableFuture<SendResult<String, byte[]>> publishPlanExecution(String tenantId, PlanExecution planExecution) {
        try {
            String topic = TopicNames.controlledPlanExecutions(tenantId);
            
            byte[] message = ProtobufUtils.serializePlanExecution(planExecution);
            if (message == null) {
                throw new RuntimeException("Failed to serialize PlanExecution");
            }
            
            String messageKey = planExecution.getHeader().getName();
            
            // Log enhanced parent relationship information
            logParentRelationshipInfo("PlanExecution", planExecution, tenantId);
            
            logger.debug("Publishing PlanExecution protobuf to topic {}: {}", topic, messageKey);
            
            ProducerRecord<String, byte[]> record = new ProducerRecord<>(topic, messageKey, message);
            return kafkaTemplate.send(record);
            
        } catch (Exception e) {
            logger.error("Failed to publish PlanExecution protobuf for tenant {}: {}", tenantId, e.getMessage(), e);
            CompletableFuture<SendResult<String, byte[]>> future = new CompletableFuture<>();
            future.completeExceptionally(e);
            return future;
        }
    }
    
    /**
     * Log enhanced parent relationship information for PlanExecution messages
     * 
     * @param messageType the type of message
     * @param planExecution the PlanExecution message
     * @param tenantId the tenant identifier
     */
    private void logParentRelationshipInfo(String messageType, PlanExecution planExecution, String tenantId) {
        if (planExecution != null) {
            var parentTaskExecIds = planExecution.getParentTaskExecIdsList();
            String parentTaskNames = planExecution.getParentTaskNames();
            
            logger.debug("{} parent relationships for tenant {}: parent_task_exec_ids={}, parent_task_names={}", 
                messageType, tenantId, parentTaskExecIds, parentTaskNames);
            
            // Log upstream task results information
            if (planExecution.hasResult()) {
                var upstreamResults = planExecution.getResult().getUpstreamTasksResultsList();
                logger.debug("{} has {} upstream task results for tenant {}", 
                    messageType, upstreamResults.size(), tenantId);
            }
        }
    }
    
    /**
     * Handle send result and log success/failure.
     * 
     * @param future the CompletableFuture from the send operation
     * @param tenantId the tenant identifier
     * @param messageId the message identifier
     * @param messageType the type of message (PlanInput/PlanExecution)
     */
    public void handleSendResult(CompletableFuture<SendResult<String, byte[]>> future, 
                                String tenantId, String messageId, String messageType) {
        future.whenComplete((result, throwable) -> {
            if (throwable != null) {
                logger.error("Failed to publish {} protobuf for tenant {} message {}: {}", 
                    messageType, tenantId, messageId, throwable.getMessage());
            } else {
                logger.debug("Successfully published {} protobuf for tenant {} message {} to topic {}", 
                    messageType, tenantId, messageId, result.getRecordMetadata().topic());
            }
        });
    }
} 