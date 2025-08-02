package com.pcallahan.agentic.taskexecutor.kafka;

import com.pcallahan.agentic.common.ProtobufUtils;
import com.pcallahan.agentic.common.TopicNames;
import agentic.task.Task.TaskExecution;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Component;

import java.util.concurrent.CompletableFuture;

/**
 * Kafka producer for TaskExecutor service.
 * Emits TaskExecution protobuf messages to task-executions-{tenantId} topics.
 */
@Component
public class TaskExecutionProducer {
    
    private static final Logger logger = LoggerFactory.getLogger(TaskExecutionProducer.class);
    
    private final KafkaTemplate<String, byte[]> kafkaTemplate;
    
    @Autowired
    public TaskExecutionProducer(KafkaTemplate<String, byte[]> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }
    
    /**
     * Publish TaskExecution protobuf message to task-executions topic.
     * 
     * @param tenantId the tenant identifier
     * @param taskExecution the TaskExecution protobuf message
     * @return CompletableFuture for the send result
     */
    public CompletableFuture<SendResult<String, byte[]>> publishTaskExecution(String tenantId, TaskExecution taskExecution) {
        try {
            String topic = TopicNames.taskExecutions(tenantId);
            
            // Serialize TaskExecution to byte array
            byte[] serializedData = ProtobufUtils.serializeTaskExecution(taskExecution);
            if (serializedData == null) {
                logger.error("Failed to serialize TaskExecution for tenant: {}", tenantId);
                CompletableFuture<SendResult<String, byte[]>> future = new CompletableFuture<>();
                future.completeExceptionally(new RuntimeException("Failed to serialize TaskExecution"));
                return future;
            }
            
            String messageKey = taskExecution.getHeader().getId();
            
            logger.debug("Publishing TaskExecution to topic {}: {}", topic, messageKey);
            
            ProducerRecord<String, byte[]> record = new ProducerRecord<>(topic, messageKey, serializedData);
            return kafkaTemplate.send(record);
            
        } catch (Exception e) {
            logger.error("Failed to publish TaskExecution for tenant {}: {}", tenantId, e.getMessage(), e);
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
     * @param taskExecutionId the task execution identifier
     */
    public void handleSendResult(CompletableFuture<SendResult<String, byte[]>> future, 
                                String tenantId, String taskExecutionId) {
        future.whenComplete((result, throwable) -> {
            if (throwable != null) {
                logger.error("Failed to publish TaskExecution for tenant {} execution {}: {}", 
                    tenantId, taskExecutionId, throwable.getMessage());
            } else {
                logger.debug("Successfully published TaskExecution for tenant {} execution {} to topic {}", 
                    tenantId, taskExecutionId, result.getRecordMetadata().topic());
            }
        });
    }
} 