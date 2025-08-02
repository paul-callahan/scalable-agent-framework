package com.pcallahan.agentic.controlplane.kafka;

import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.common.ProtobufUtils;
import agentic.task.Task.TaskResult;
import agentic.plan.Plan.PlanResult;
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
 * - TaskResult messages to task-results-{tenantId} topics (for PlanExecutor to consume)
 * - PlanResult messages to plan-results-{tenantId} topics (for TaskExecutor to consume)
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
     * Publish TaskResult protobuf to task-results topic for PlanExecutor to consume.
     * 
     * @param tenantId the tenant identifier
     * @param taskResult the TaskResult protobuf message
     * @return CompletableFuture for the send result
     */
    public CompletableFuture<SendResult<String, byte[]>> publishTaskResult(String tenantId, TaskResult taskResult) {
        try {
            String topic = TopicNames.taskResults(tenantId);
            
            byte[] message = ProtobufUtils.serializeTaskResult(taskResult);
            if (message == null) {
                throw new RuntimeException("Failed to serialize TaskResult");
            }
            
            String messageId = "task-result-" + System.currentTimeMillis();
            
            logger.debug("Publishing TaskResult protobuf to topic {}: {}", topic, messageId);
            
            ProducerRecord<String, byte[]> record = new ProducerRecord<>(topic, messageId, message);
            return kafkaTemplate.send(record);
            
        } catch (Exception e) {
            logger.error("Failed to publish TaskResult protobuf for tenant {}: {}", tenantId, e.getMessage(), e);
            CompletableFuture<SendResult<String, byte[]>> future = new CompletableFuture<>();
            future.completeExceptionally(e);
            return future;
        }
    }
    
    /**
     * Publish PlanResult protobuf to plan-results topic for TaskExecutor to consume.
     * 
     * @param tenantId the tenant identifier
     * @param planResult the PlanResult protobuf message
     * @return CompletableFuture for the send result
     */
    public CompletableFuture<SendResult<String, byte[]>> publishPlanResult(String tenantId, PlanResult planResult) {
        try {
            String topic = TopicNames.planResults(tenantId);
            
            byte[] message = ProtobufUtils.serializePlanResult(planResult);
            if (message == null) {
                throw new RuntimeException("Failed to serialize PlanResult");
            }
            
            String messageId = "plan-result-" + System.currentTimeMillis();
            
            logger.debug("Publishing PlanResult protobuf to topic {}: {}", topic, messageId);
            
            ProducerRecord<String, byte[]> record = new ProducerRecord<>(topic, messageId, message);
            return kafkaTemplate.send(record);
            
        } catch (Exception e) {
            logger.error("Failed to publish PlanResult protobuf for tenant {}: {}", tenantId, e.getMessage(), e);
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
     * @param messageType the type of message (TaskResult/PlanResult)
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