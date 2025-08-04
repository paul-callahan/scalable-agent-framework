package com.pcallahan.agentic.planexecutor.kafka;

import com.pcallahan.agentic.common.ProtobufUtils;
import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.planexecutor.service.PlanExecutorService;
import agentic.task.Task.TaskExecution;
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
 * Kafka listener for TaskExecution protobuf messages from control plane.
 * Consumes messages from controlled-task-executions-{tenantId} topics and executes plans.
 */
@Component
public class TaskResultListener {
    
    private static final Logger logger = LoggerFactory.getLogger(TaskResultListener.class);
    
    private final PlanExecutorService planExecutorService;
    
    @Autowired
    public TaskResultListener(PlanExecutorService planExecutorService) {
        this.planExecutorService = planExecutorService;
    }
    
    /**
     * Listen for TaskExecution protobuf messages from controlled-task-executions topics.
     * 
     * @param record the Kafka consumer record
     * @param topic the topic name
     * @param acknowledgment manual acknowledgment
     */
    @KafkaListener(
        topics = "#{@kafkaTopicPatterns.controlledTaskExecutionsPattern}",
        groupId = "plan-executor-controlled-task-executions",
        containerFactory = "tenantAwareKafkaListenerContainerFactory"
    )
    public void handleTaskExecution(
            ConsumerRecord<String, byte[]> record,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            Acknowledgment acknowledgment) {
        
        try {
            logger.debug("Received TaskExecution protobuf message from topic: {}", topic);
            
            // Deserialize protobuf message
            TaskExecution taskExecution = ProtobufUtils.deserializeTaskExecution(record.value());
            if (taskExecution == null) {
                logger.error("Failed to deserialize TaskExecution message from topic: {}", topic);
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
            
            // Store TaskExecution in cache for upstream reference
            planExecutorService.cacheTaskExecution(taskExecution);
            
            // Execute plans based on TaskExecution
            boolean success = planExecutorService.executePlansFromTaskExecution(taskExecution, tenantId);
            
            if (success) {
                logger.info("Successfully executed plans from TaskExecution protobuf for tenant: {}", tenantId);
            } else {
                logger.error("Failed to execute plans from TaskExecution protobuf for tenant: {}", tenantId);
            }
            
            // Acknowledge the message
            acknowledgment.acknowledge();
            
        } catch (Exception e) {
            logger.error("Error processing TaskExecution protobuf message from topic {}: {}", topic, e.getMessage(), e);
            // Don't acknowledge on error to allow retry
        }
    }
} 