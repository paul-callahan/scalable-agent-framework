package com.pcallahan.agentic.graphbuilder;

import com.pcallahan.agentic.common.graph.AgentGraph;
import com.pcallahan.agentic.common.graph.Plan;
import com.pcallahan.agentic.common.graph.Task;
import org.graphper.parser.DotParser;
import org.graphper.api.Graphviz;
import org.graphper.api.Node;
import org.graphper.api.Edge;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Graph parser implementation backed by Graphviz dot files.
 */
public class GraphvizGraphParser implements GraphParser {
    @Override
    public AgentGraph parse(Path specFile) throws GraphParseException {
        Graphviz graph;
        try {
            graph = DotParser.parse(Files.newBufferedReader(specFile));
        } catch (IOException e) {
            throw new GraphParseException("Failed to read spec file", e);
        }

        Map<String, Path> planSources = new HashMap<>();
        Map<String, Path> taskSources = new HashMap<>();

        for (Node node : graph.nodes()) {
            String id = node.id();
            String type = node.get("type");
            if ("plan".equals(type)) {
                String src = node.get("plan_source");
                planSources.put(id, specFile.getParent().resolve(src));
            } else if ("task".equals(type)) {
                String src = node.get("task_source");
                taskSources.put(id, specFile.getParent().resolve(src));
            } else {
                throw new GraphParseException("Unknown node type for " + id);
            }
        }

        Map<String, List<String>> planToTasks = new HashMap<>();
        Map<String, String> taskToPlan = new HashMap<>();

        for (Edge edge : graph.edges()) {
            String from = edge.from().id();
            String to = edge.to().id();
            if (planSources.containsKey(from) && taskSources.containsKey(to)) {
                planToTasks.computeIfAbsent(from, k -> new ArrayList<>()).add(to);
                if (taskToPlan.put(to, from) != null) {
                    throw new GraphParseException("Task " + to + " has multiple upstream plans");
                }
            } else if (taskSources.containsKey(from) && planSources.containsKey(to)) {
                if (taskToPlan.put(from, to) != null) {
                    throw new GraphParseException("Task " + from + " points to multiple plans");
                }
                planToTasks.computeIfAbsent(to, k -> new ArrayList<>());
            } else {
                throw new GraphParseException("Edges must connect plans and tasks");
            }
        }

        Map<String, List<String>> upstreamTasksByPlan = new HashMap<>();
        for (Map.Entry<String, String> entry : taskToPlan.entrySet()) {
            upstreamTasksByPlan.computeIfAbsent(entry.getValue(), k -> new ArrayList<>()).add(entry.getKey());
        }

        List<Task> tasks = new ArrayList<>();
        for (Map.Entry<String, Path> e : taskSources.entrySet()) {
            String upstream = taskToPlan.get(e.getKey());
            if (upstream == null) {
                throw new GraphParseException("Task " + e.getKey() + " is unconnected");
            }
            tasks.add(new Task(e.getKey(), e.getValue(), upstream));
        }

        List<Plan> plans = new ArrayList<>();
        for (Map.Entry<String, Path> e : planSources.entrySet()) {
            List<String> upstream = upstreamTasksByPlan.getOrDefault(e.getKey(), List.of());
            if (!planToTasks.containsKey(e.getKey()) && upstream.isEmpty()) {
                throw new GraphParseException("Plan " + e.getKey() + " is unconnected");
            }
            planToTasks.putIfAbsent(e.getKey(), new ArrayList<>());
            plans.add(new Plan(e.getKey(), e.getValue(), upstream));
        }

        return new AgentGraph(plans, tasks, planToTasks, taskToPlan);
    }
}
