package com.pcallahan.agentic.controlplane.kafka;

import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.common.ProtobufUtils;
import agentic.task.Task.TaskExecution;
import agentic.plan.Plan.PlanExecution;
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
 * - TaskExecution messages to controlled-task-executions-{tenantId} topics (for PlanExecutor to consume)
 * - PlanExecution messages to controlled-plan-executions-{tenantId} topics (for TaskExecutor to consume)
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
     * Publish TaskExecution protobuf to controlled-task-executions topic for PlanExecutor to consume.
     * 
     * @param tenantId the tenant identifier
     * @param taskExecution the TaskExecution protobuf message
     * @return CompletableFuture for the send result
     */
    public CompletableFuture<SendResult<String, byte[]>> publishTaskExecution(String tenantId, TaskExecution taskExecution) {
        try {
            String topic = TopicNames.controlledTaskExecutions(tenantId);
            
            byte[] message = ProtobufUtils.serializeTaskExecution(taskExecution);
            if (message == null) {
                throw new RuntimeException("Failed to serialize TaskExecution");
            }
            
            String messageId = "task-execution-" + System.currentTimeMillis();
            
            logger.debug("Publishing TaskExecution protobuf to topic {}: {}", topic, messageId);
            
            ProducerRecord<String, byte[]> record = new ProducerRecord<>(topic, messageId, message);
            return kafkaTemplate.send(record);
            
        } catch (Exception e) {
            logger.error("Failed to publish TaskExecution protobuf for tenant {}: {}", tenantId, e.getMessage(), e);
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
            
            String messageId = "plan-execution-" + System.currentTimeMillis();
            
            logger.debug("Publishing PlanExecution protobuf to topic {}: {}", topic, messageId);
            
            ProducerRecord<String, byte[]> record = new ProducerRecord<>(topic, messageId, message);
            return kafkaTemplate.send(record);
            
        } catch (Exception e) {
            logger.error("Failed to publish PlanExecution protobuf for tenant {}: {}", tenantId, e.getMessage(), e);
            CompletableFuture<SendResult<String, byte[]>> future = new CompletableFuture<>();
            future.completeExceptionally(e);
            return future;
        }
    }
    
    /**
     * Handle send result and log success/failure.
     * 
     * @param future the CompletableFuture from the send operation
     * @param tenantId the tenant identifier
     * @param messageId the message identifier
     * @param messageType the type of message (TaskExecution/PlanExecution)
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