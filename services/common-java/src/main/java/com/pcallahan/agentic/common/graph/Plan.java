package com.pcallahan.agentic.common.graph;

import java.nio.file.Path;
import java.util.List;
import java.util.Objects;

/**
 * Representation of a plan within an agent graph.
 */
public record Plan(String name, Path planSource, List<String> upstreamTaskIds) {
    public Plan {
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(planSource, "planSource");
        upstreamTaskIds = upstreamTaskIds == null ? List.of() : List.copyOf(upstreamTaskIds);
    }
}
