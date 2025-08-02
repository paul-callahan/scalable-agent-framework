package com.pcallahan.agentic.taskexecutor.kafka;

import com.pcallahan.agentic.common.ProtobufUtils;
import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.taskexecutor.service.TaskExecutorService;
import agentic.plan.Plan.PlanResult;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

/**
 * Kafka listener for PlanResult protobuf messages from control plane.
 * Consumes messages from plan-results-{tenantId} topics and executes tasks.
 */
@Component
public class PlanResultListener {
    
    private static final Logger logger = LoggerFactory.getLogger(PlanResultListener.class);
    
    private final TaskExecutorService taskExecutorService;
    private final TaskExecutionProducer taskExecutionProducer;
    
    @Autowired
    public PlanResultListener(TaskExecutorService taskExecutorService, 
                            TaskExecutionProducer taskExecutionProducer) {
        this.taskExecutorService = taskExecutorService;
        this.taskExecutionProducer = taskExecutionProducer;
    }
    
    /**
     * Listen for PlanResult protobuf messages from plan-results topics.
     * 
     * @param record the Kafka consumer record
     * @param topic the topic name
     * @param acknowledgment manual acknowledgment
     */
    @KafkaListener(
        topics = "#{@kafkaTopicPatterns.planResultsPattern}",
        groupId = "task-executor-plan-results",
        containerFactory = "tenantAwareKafkaListenerContainerFactory"
    )
    public void handlePlanResult(
            ConsumerRecord<String, byte[]> record,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            Acknowledgment acknowledgment) {
        
        try {
            logger.debug("Received PlanResult protobuf message from topic: {}", topic);
            
            // Deserialize protobuf message
            PlanResult planResult = ProtobufUtils.deserializePlanResult(record.value());
            if (planResult == null) {
                logger.error("Failed to deserialize PlanResult message from topic: {}", topic);
                acknowledgment.acknowledge();
                return;
            }
            
            // Extract tenant ID from topic name
            String tenantId = TopicNames.extractTenantId(topic);
            if (tenantId == null) {
                logger.error("Could not extract tenant ID from topic: {}", topic);
                acknowledgment.acknowledge();
                return;
            }
            
            // Execute tasks based on PlanResult
            boolean success = taskExecutorService.executeTasksFromPlan(planResult, tenantId);
            
            if (success) {
                logger.info("Successfully executed tasks from PlanResult protobuf for tenant: {}", tenantId);
            } else {
                logger.error("Failed to execute tasks from PlanResult protobuf for tenant: {}", tenantId);
            }
            
            // Acknowledge the message
            acknowledgment.acknowledge();
            
        } catch (Exception e) {
            logger.error("Error processing PlanResult protobuf message from topic {}: {}", topic, e.getMessage(), e);
            // Don't acknowledge on error to allow retry
        }
    }
} 