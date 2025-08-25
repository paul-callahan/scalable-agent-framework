package com.pcallahan.agentic.graphbuilder;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

/**
 * Test application configuration for integration tests.
 */
@SpringBootApplication(scanBasePackages = {
    "com.pcallahan.agentic"
})
@EnableJpaRepositories(basePackages = {
    "com.pcallahan.agentic.graph.repository",
    "com.pcallahan.agentic.graphbuilder.repository"
})
@EntityScan(basePackages = {
    "com.pcallahan.agentic.graph.entity",
    "com.pcallahan.agentic.graphbuilder.entity"
})
public class TestApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(TestApplication.class, args);
    }
}