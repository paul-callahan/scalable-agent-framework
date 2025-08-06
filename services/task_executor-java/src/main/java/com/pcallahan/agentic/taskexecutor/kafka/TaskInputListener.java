package com.pcallahan.agentic.taskexecutor.kafka;

import com.pcallahan.agentic.common.ProtobufUtils;
import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.taskexecutor.kafka.TaskExecutionProducer;
import com.pcallahan.agentic.taskexecutor.service.TaskExecutorService;
import io.arl.proto.model.Plan.TaskInput;
import io.arl.proto.model.Plan.PlanExecution;
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
 * Kafka listener for TaskInput protobuf messages from control plane.
 * Consumes messages from task-inputs-{tenantId} topics and executes tasks.
 */
@Component
public class TaskInputListener {
    
    private static final Logger logger = LoggerFactory.getLogger(TaskInputListener.class);
    
    private final TaskExecutorService taskExecutorService;
    private final TaskExecutionProducer taskExecutionProducer;
    
    @Autowired
    public TaskInputListener(TaskExecutorService taskExecutorService, 
                           TaskExecutionProducer taskExecutionProducer) {
        this.taskExecutorService = taskExecutorService;
        this.taskExecutionProducer = taskExecutionProducer;
    }
    
    /**
     * Listen for TaskInput protobuf messages from task-inputs topics.
     * 
     * @param record the Kafka consumer record
     * @param topic the topic name
     * @param acknowledgment manual acknowledgment
     */
    @KafkaListener(
        topics = "#{@kafkaTopicPatterns.taskInputsPattern}",
        groupId = "task-executor-task-inputs",
        containerFactory = "tenantAwareKafkaListenerContainerFactory"
    )
    public void handleTaskInput(
            ConsumerRecord<String, byte[]> record,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            Acknowledgment acknowledgment) {
        
        try {
            logger.debug("Received TaskInput protobuf message from topic: {}", topic);
            
            // Deserialize protobuf message
            TaskInput taskInput = ProtobufUtils.deserializeTaskInput(record.value());
            if (taskInput == null) {
                logger.error("Failed to deserialize TaskInput message from topic: {}", topic);
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
            
            // Extract PlanExecution from TaskInput
            PlanExecution planExecution = taskInput.getPlanExecution();
            if (planExecution == null) {
                logger.error("TaskInput does not contain PlanExecution for tenant: {}", tenantId);
                acknowledgment.acknowledge();
                return;
            }
            
            logger.debug("Processing TaskInput for task '{}' with input_id '{}' for tenant: {}", 
                taskInput.getTaskName(), taskInput.getInputId(), tenantId);
            
            // Execute tasks based on PlanExecution from TaskInput
            boolean success = taskExecutorService.executeTasksFromPlanExecution(planExecution, tenantId);
            
            if (success) {
                logger.info("Successfully executed tasks from TaskInput protobuf for task '{}' tenant: {}", 
                    taskInput.getTaskName(), tenantId);
            } else {
                logger.error("Failed to execute tasks from TaskInput protobuf for task '{}' tenant: {}", 
                    taskInput.getTaskName(), tenantId);
            }
            
            // Acknowledge the message
            acknowledgment.acknowledge();
            
        } catch (Exception e) {
            logger.error("Error processing TaskInput protobuf message from topic {}: {}", topic, e.getMessage(), e);
            // Don't acknowledge on error to allow retry
        }
    }
} 