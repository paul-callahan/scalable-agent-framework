package com.pcallahan.agentic.common;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.Map;

/**
 * Configuration class for Kafka topic patterns used across all microservices.
 * 
 * This class reads topic patterns from application.yml and provides them as Spring beans
 * for use in @KafkaListener annotations. The patterns support tenant-aware topic naming
 * with wildcards for dynamic subscription.
 */
@Configuration
@ConfigurationProperties(prefix = "kafka.topic-patterns")
public class KafkaTopicPatterns {
    
    private static final Logger logger = LoggerFactory.getLogger(KafkaTopicPatterns.class);
    
    // Topic patterns for different message types
    private String taskExecutions = "task-executions-.*";
    private String planExecutions = "plan-executions-.*";
    private String taskControl = "task-control-.*";
    private String planControl = "plan-control-.*";
    private String taskResults = "task-results-.*";
    private String planResults = "plan-results-.*";
    
    // Getters and setters
    public String getTaskExecutionsPattern() {
        return taskExecutions;
    }
    
    public void setTaskExecutions(String taskExecutions) {
        this.taskExecutions = taskExecutions;
        logger.debug("Set task executions pattern: {}", taskExecutions);
    }
    
    public String getPlanExecutionsPattern() {
        return planExecutions;
    }
    
    public void setPlanExecutions(String planExecutions) {
        this.planExecutions = planExecutions;
        logger.debug("Set plan executions pattern: {}", planExecutions);
    }
    
    public String getTaskControlPattern() {
        return taskControl;
    }
    
    public void setTaskControl(String taskControl) {
        this.taskControl = taskControl;
        logger.debug("Set task control pattern: {}", taskControl);
    }
    
    public String getPlanControlPattern() {
        return planControl;
    }
    
    public void setPlanControl(String planControl) {
        this.planControl = planControl;
        logger.debug("Set plan control pattern: {}", planControl);
    }
    
    public String getTaskResultsPattern() {
        return taskResults;
    }
    
    public void setTaskResults(String taskResults) {
        this.taskResults = taskResults;
        logger.debug("Set task results pattern: {}", taskResults);
    }
    
    public String getPlanResultsPattern() {
        return planResults;
    }
    
    public void setPlanResults(String planResults) {
        this.planResults = planResults;
        logger.debug("Set plan results pattern: {}", planResults);
    }
    
    /**
     * Get all topic patterns as a map for dynamic configuration.
     * 
     * @return map of pattern names to pattern values
     */
    public Map<String, String> getAllPatterns() {
        return Map.of(
            "taskExecutions", taskExecutions,
            "planExecutions", planExecutions,
            "taskControl", taskControl,
            "planControl", planControl,
            "taskResults", taskResults,
            "planResults", planResults
        );
    }
    
    /**
     * Validate that all patterns are properly configured.
     * 
     * @return true if all patterns are valid, false otherwise
     */
    public boolean validatePatterns() {
        boolean isValid = true;
        
        if (taskExecutions == null || taskExecutions.isEmpty()) {
            logger.error("Task executions pattern is not configured");
            isValid = false;
        }
        
        if (planExecutions == null || planExecutions.isEmpty()) {
            logger.error("Plan executions pattern is not configured");
            isValid = false;
        }
        
        if (taskControl == null || taskControl.isEmpty()) {
            logger.error("Task control pattern is not configured");
            isValid = false;
        }
        
        if (planControl == null || planControl.isEmpty()) {
            logger.error("Plan control pattern is not configured");
            isValid = false;
        }
        
        if (taskResults == null || taskResults.isEmpty()) {
            logger.error("Task results pattern is not configured");
            isValid = false;
        }
        
        if (planResults == null || planResults.isEmpty()) {
            logger.error("Plan results pattern is not configured");
            isValid = false;
        }
        
        if (isValid) {
            logger.info("All Kafka topic patterns are properly configured");
        }
        
        return isValid;
    }
} 