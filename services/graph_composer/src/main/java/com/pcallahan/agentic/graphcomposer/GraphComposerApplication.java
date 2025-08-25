package com.pcallahan.agentic.graphcomposer;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

/**
 * Main Spring Boot application class for the Graph Composer service.
 * This service provides a visual editor for creating and managing Agent Graphs
 * in the Agentic Framework.
 */
@SpringBootApplication
@EntityScan(basePackages = {
    "com.pcallahan.agentic.graphcomposer.entity",
    "com.pcallahan.agentic.graph.entity"
})
@EnableJpaRepositories(basePackages = {
    "com.pcallahan.agentic.graphcomposer.repository",
    "com.pcallahan.agentic.graph.repository"
})
public class GraphComposerApplication {

    public static void main(String[] args) {
        SpringApplication.run(GraphComposerApplication.class, args);
    }
}