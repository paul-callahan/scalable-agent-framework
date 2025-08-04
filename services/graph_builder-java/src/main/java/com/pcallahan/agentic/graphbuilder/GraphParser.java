package com.pcallahan.agentic.graphbuilder;

import com.pcallahan.agentic.common.graph.AgentGraph;

import java.nio.file.Path;

/**
 * Parses a graph specification into an {@link AgentGraph}.
 */
public interface GraphParser {
    AgentGraph parse(Path specFile) throws GraphParseException;
}
