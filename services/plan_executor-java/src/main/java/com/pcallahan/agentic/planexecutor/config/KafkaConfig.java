package com.pcallahan.agentic.planexecutor.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Kafka configuration for the Plan Executor service.
 * 
 * This configuration provides:
 * - ObjectMapper configuration for JSON serialization
 * - Integration with tenant-aware Kafka configuration from common module
 */
@Configuration
public class KafkaConfig {
    
    /**
     * Configure ObjectMapper for JSON serialization.
     */
    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        return mapper;
    }
} 