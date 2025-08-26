package com.pcallahan.agentic.graphcomposer.dto;

/**
 * Enumeration representing the status of an Agent Graph.
 * Used to track the lifecycle state of graphs in the system.
 */
public enum GraphStatus {
    /**
     * Graph has been created but not yet submitted for execution
     */
    NEW,
    
    /**
     * Graph is currently being executed
     */
    RUNNING,
    
    /**
     * Graph execution has been stopped or completed successfully
     */
    STOPPED,
    
    /**
     * Graph execution encountered an error
     */
    ERROR
}