package com.pcallahan.agentic.common.graph;

import java.util.List;
import java.util.Map;

/**
 * Immutable representation of an agent graph containing plans, tasks and edges
 * between them.
 */
public final class AgentGraph {
    private final List<Plan> plans;
    private final List<Task> tasks;
    private final Map<String, List<String>> planToTasks;
    private final Map<String, String> taskToPlan;

    public AgentGraph(List<Plan> plans, List<Task> tasks,
                      Map<String, List<String>> planToTasks,
                      Map<String, String> taskToPlan) {
        this.plans = List.copyOf(plans);
        this.tasks = List.copyOf(tasks);
        this.planToTasks = Map.copyOf(planToTasks);
        this.taskToPlan = Map.copyOf(taskToPlan);
    }

    public List<Plan> getPlans() {
        return plans;
    }

    public List<Task> getTasks() {
        return tasks;
    }

    public Map<String, List<String>> getPlanToTasks() {
        return planToTasks;
    }

    public Map<String, String> getTaskToPlan() {
        return taskToPlan;
    }
}
