package com.pcallahan.agentic.planexecutor;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * Main Spring Boot application class for the Plan Executor microservice.
 * 
 * This service is responsible for:
 * - Consuming plan execution messages from Kafka
 * - Executing plans based on their type and parameters
 * - Publishing plan results back to Kafka
 * - Managing plan execution lifecycle and error handling
 */
@SpringBootApplication
@EnableKafka
public class PlanExecutorApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(PlanExecutorApplication.class, args);
    }
} 