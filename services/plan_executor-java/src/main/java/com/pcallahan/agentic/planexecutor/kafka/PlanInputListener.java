package com.pcallahan.agentic.planexecutor.kafka;

import com.pcallahan.agentic.common.ProtobufUtils;
import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.planexecutor.service.PlanExecutorService;
import io.arl.proto.model.Plan.PlanInput;
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
 * Kafka listener for PlanInput protobuf messages from control plane.
 * Consumes messages from plan-inputs-{tenantId} topics and executes plans.
 */
@Component
public class PlanInputListener {
    
    private static final Logger logger = LoggerFactory.getLogger(PlanInputListener.class);
    
    private final PlanExecutorService planExecutorService;
    
    @Autowired
    public PlanInputListener(PlanExecutorService planExecutorService) {
        this.planExecutorService = planExecutorService;
    }
    
    /**
     * Listen for PlanInput protobuf messages from plan-inputs topics.
     * 
     * @param record the Kafka consumer record
     * @param topic the topic name
     * @param acknowledgment manual acknowledgment
     */
    @KafkaListener(
        topics = "#{@kafkaTopicPatterns.planInputsPattern}",
        groupId = "plan-executor-plan-inputs",
        containerFactory = "tenantAwareKafkaListenerContainerFactory"
    )
    public void handlePlanInput(
            ConsumerRecord<String, byte[]> record,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            Acknowledgment acknowledgment) {
        
        try {
            logger.debug("Received PlanInput protobuf message from topic: {}", topic);
            
            // Deserialize protobuf message
            PlanInput planInput = ProtobufUtils.deserializePlanInput(record.value());
            if (planInput == null) {
                logger.error("Failed to deserialize PlanInput message from topic: {}", topic);
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
            
            // Note: PlanInput is processed directly without caching for stateless design
            
            // Execute plans based on PlanInput
            boolean success = planExecutorService.executePlansFromPlanInput(planInput, tenantId);
            
            if (success) {
                logger.info("Successfully executed plans from PlanInput protobuf for tenant: {}", tenantId);
            } else {
                logger.error("Failed to execute plans from PlanInput protobuf for tenant: {}", tenantId);
            }
            
            // Acknowledge the message
            acknowledgment.acknowledge();
            
        } catch (Exception e) {
            logger.error("Error processing PlanInput protobuf message from topic {}: {}", topic, e.getMessage(), e);
            // Don't acknowledge on error to allow retry
        }
    }
} 