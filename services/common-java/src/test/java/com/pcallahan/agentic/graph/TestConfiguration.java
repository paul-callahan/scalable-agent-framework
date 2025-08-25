package com.pcallahan.agentic.graph;

import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

/**
 * Test configuration for JPA tests.
 */
@SpringBootApplication
@EntityScan(basePackages = "com.pcallahan.agentic.graph.entity")
@EnableJpaRepositories(basePackages = "com.pcallahan.agentic.graph.repository")
public class TestConfiguration {
}