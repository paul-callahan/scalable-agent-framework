package com.pcallahan.agentic.dataplane.kafka;

import com.pcallahan.agentic.common.ProtobufUtils;
import com.pcallahan.agentic.common.TopicNames;
import com.pcallahan.agentic.dataplane.service.PersistenceService;
import agentic.plan.Plan.PlanExecution;
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
 * Kafka listener for PlanExecution messages from plan-executors.
 * Consumes messages from plan-executions-{tenantId} topics and persists them to the database.
 * Publishes PlanExecution protobuf messages to persisted-plan-executions-{tenantId} topics for the control plane.
 */
@Component
public class PlanExecutionListener {
    
    private static final Logger logger = LoggerFactory.getLogger(PlanExecutionListener.class);
    
    private final PersistenceService persistenceService;
    private final ControlPlaneProducer controlPlaneProducer;
    
    @Autowired
    public PlanExecutionListener(PersistenceService persistenceService, 
                               ControlPlaneProducer controlPlaneProducer) {
        this.persistenceService = persistenceService;
        this.controlPlaneProducer = controlPlaneProducer;
    }
    
    /**
     * Listen for PlanExecution messages from plan-executions topics.
     * 
     * @param record the Kafka consumer record
     * @param topic the topic name
     * @param acknowledgment manual acknowledgment
     */
    @KafkaListener(
        topics = "#{@kafkaTopicPatterns.planExecutionsPattern}",
        groupId = "data-plane-plan-executions",
        containerFactory = "tenantAwareKafkaListenerContainerFactory"
    )
    public void handlePlanExecution(
            ConsumerRecord<String, byte[]> record,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            Acknowledgment acknowledgment) {
        
        try {
            logger.debug("Received PlanExecution message from topic: {}", topic);
            
            // Extract tenant ID from topic name
            String tenantId = TopicNames.extractTenantId(topic);
            if (tenantId == null) {
                logger.error("Could not extract tenant ID from topic: {}", topic);
                acknowledgment.acknowledge();
                return;
            }
            
            // Deserialize protobuf message
            PlanExecution planExecution = ProtobufUtils.deserializePlanExecution(record.value());
            if (planExecution == null) {
                logger.error("Failed to deserialize PlanExecution message from topic: {}", topic);
                acknowledgment.acknowledge();
                return;
            }
            
            // Validate message
            if (!ProtobufUtils.isValidMessage(planExecution)) {
                logger.error("Invalid PlanExecution message received from topic: {}", topic);
                acknowledgment.acknowledge();
                return;
            }
            
            // Process the plan execution and persist to database
            boolean success = persistenceService.processPlanExecution(planExecution, tenantId);
            
            if (success) {
                logger.debug("Successfully processed PlanExecution {} for tenant {}", 
                    planExecution.getHeader().getId(), tenantId);
                
                // Publish PlanExecution protobuf message to control plane
                controlPlaneProducer.publishPlanExecution(tenantId, planExecution);
                    
            } else {
                logger.error("Failed to process PlanExecution {} for tenant {}", 
                    planExecution.getHeader().getId(), tenantId);
            }
            
            // Acknowledge the message
            acknowledgment.acknowledge();
            
        } catch (Exception e) {
            logger.error("Error processing PlanExecution message from topic {}: {}", topic, e.getMessage(), e);
            // Don't acknowledge on error to allow retry
        }
    }
} 