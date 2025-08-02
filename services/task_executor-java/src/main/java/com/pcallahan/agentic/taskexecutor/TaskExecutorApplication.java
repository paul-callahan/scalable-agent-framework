package com.pcallahan.agentic.taskexecutor;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * Main Spring Boot application class for the Task Executor microservice.
 * 
 * This service is responsible for:
 * - Consuming task execution messages from Kafka
 * - Executing tasks based on their type and parameters
 * - Publishing task results back to Kafka
 * - Managing task execution lifecycle and error handling
 */
@SpringBootApplication
@EnableKafka
public class TaskExecutorApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(TaskExecutorApplication.class, args);
    }
} 