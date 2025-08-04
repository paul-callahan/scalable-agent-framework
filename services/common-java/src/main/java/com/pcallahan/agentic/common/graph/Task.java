package com.pcallahan.agentic.common.graph;

import java.nio.file.Path;
import java.util.Objects;

/**
 * Representation of a task within an agent graph.
 */
public record Task(String name, Path taskSource, String upstreamPlanId) {
    public Task {
        Objects.requireNonNull(name, "name");
        Objects.requireNonNull(taskSource, "taskSource");
        Objects.requireNonNull(upstreamPlanId, "upstreamPlanId");
    }
}
