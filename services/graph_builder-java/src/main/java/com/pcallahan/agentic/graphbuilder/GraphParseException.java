package com.pcallahan.agentic.graphbuilder;

/**
 * Exception thrown when a graph specification cannot be parsed.
 */
public class GraphParseException extends RuntimeException {
    public GraphParseException(String message) {
        super(message);
    }

    public GraphParseException(String message, Throwable cause) {
        super(message, cause);
    }
}
