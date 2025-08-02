package com.pcallahan.agentic.planexecutor.kafka;

import com.pcallahan.agentic.common.ProtobufUtils;
import com.pcallahan.agentic.common.TopicNames;
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
 * Kafka producer for PlanExecutor service.
 * Emits PlanExecution protobuf messages to plan-executions-{tenantId} topics.
 */
@Component
public class PlanExecutionProducer {
    
    private static final Logger logger = LoggerFactory.getLogger(PlanExecutionProducer.class);
    
    private final KafkaTemplate<String, byte[]> kafkaTemplate;
    
    @Autowired
    public PlanExecutionProducer(KafkaTemplate<String, byte[]> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }
    
    /**
     * Publish PlanExecution protobuf message to plan-executions topic.
     * 
     * @param tenantId the tenant identifier
     * @param planExecution the PlanExecution protobuf message
     * @return CompletableFuture for the send result
     */
    public CompletableFuture<SendResult<String, byte[]>> publishPlanExecution(String tenantId, PlanExecution planExecution) {
        try {
            String topic = TopicNames.planExecutions(tenantId);
            
            // Serialize PlanExecution to byte array
            byte[] serializedData = ProtobufUtils.serializePlanExecution(planExecution);
            if (serializedData == null) {
                logger.error("Failed to serialize PlanExecution for tenant: {}", tenantId);
                CompletableFuture<SendResult<String, byte[]>> future = new CompletableFuture<>();
                future.completeExceptionally(new RuntimeException("Failed to serialize PlanExecution"));
                return future;
            }
            
            String messageKey = planExecution.getHeader().getId();
            
            logger.debug("Publishing PlanExecution to topic {}: {}", topic, messageKey);
            
            ProducerRecord<String, byte[]> record = new ProducerRecord<>(topic, messageKey, serializedData);
            return kafkaTemplate.send(record);
            
        } catch (Exception e) {
            logger.error("Failed to publish PlanExecution for tenant {}: {}", tenantId, e.getMessage(), e);
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
     * @param planExecutionId the plan execution identifier
     */
    public void handleSendResult(CompletableFuture<SendResult<String, byte[]>> future, 
                                String tenantId, String planExecutionId) {
        future.whenComplete((result, throwable) -> {
            if (throwable != null) {
                logger.error("Failed to publish PlanExecution for tenant {} execution {}: {}", 
                    tenantId, planExecutionId, throwable.getMessage());
            } else {
                logger.debug("Successfully published PlanExecution for tenant {} execution {} to topic {}", 
                    tenantId, planExecutionId, result.getRecordMetadata().topic());
            }
        });
    }
} 