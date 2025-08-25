package com.pcallahan.agentic.graphbuilder.parser;

import com.pcallahan.agentic.graph.model.AgentGraph;
import com.pcallahan.agentic.graph.model.Plan;
import com.pcallahan.agentic.graph.model.Task;
import com.pcallahan.agentic.graph.exception.GraphParsingException;
import com.pcallahan.agentic.graph.exception.GraphValidationException;
import com.pcallahan.agentic.graphbuilder.validation.GraphValidator;
import guru.nidi.graphviz.engine.Graphviz;
import guru.nidi.graphviz.model.MutableGraph;
import guru.nidi.graphviz.model.MutableNode;
import guru.nidi.graphviz.parse.Parser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

/**
 * GraphViz DOT format parser for agent graph specifications.
 * 
 * <p>This parser reads GraphViz DOT files and constructs AgentGraph objects.
 * It expects the DOT file to define nodes representing plans and tasks, with
 * edges representing the data flow between them.</p>
 * 
 * <p>The parser identifies plans and tasks based on explicit node attributes:
 * - Plans must have <code>type="plan"</code> attribute
 * - Tasks must have <code>type="task"</code> attribute
 * 
 * Node names are used as identifiers and should be valid Java identifiers.
 * The parser validates that all referenced nodes have corresponding
 * Python subproject directories with the required files.</p>
 */
public class GraphVizDotParser implements GraphParser {
    
    private static final Logger logger = LoggerFactory.getLogger(GraphVizDotParser.class);
    
    private static final String PLANS_DIR = "plans";
    private static final String TASKS_DIR = "tasks";
    
    /**
     * Intermediate data structure to hold task metadata before creating Task objects.
     */
    private static class TaskMetadata {
        private final String name;
        private final Path taskSource;
        private final String label;
        
        public TaskMetadata(String name, Path taskSource, String label) {
            this.name = name;
            this.taskSource = taskSource;
            this.label = label;
        }
        
        public String name() { return name; }
        public Path taskSource() { return taskSource; }
        public String label() { return label; }
    }
    
    @Override
    public AgentGraph parse(Path specificationDirectory) throws GraphParsingException, GraphValidationException {
        logger.info("Parsing GraphViz DOT specification from directory: {}", specificationDirectory);
        
        // Find the DOT file
        Path dotFile = findDotFile(specificationDirectory);
        logger.debug("Found DOT file: {}", dotFile);
        
        // Parse the DOT file using the GraphViz library
        MutableGraph dotGraph = parseDotFile(dotFile);
        logger.debug("Parsed graph with {} nodes", dotGraph.nodes().size());
        
        // Extract the graph name
        String graphName = extractGraphName(dotGraph, dotFile.getFileName().toString());
        logger.debug("Extracted graph name: {}", graphName);
        
        // Identify plans and tasks
        Map<String, Plan> plans = new HashMap<>();
        Map<String, TaskMetadata> taskMetadata = new HashMap<>();
        Map<String, Set<String>> planToTasks = new HashMap<>();
        Map<String, String> taskToPlan = new HashMap<>();
        Map<String, Set<String>> planToUpstreamTasks = new HashMap<>();
        
        // Process each node to identify plans and collect task metadata
        for (MutableNode node : dotGraph.nodes()) {
            String nodeName = node.name().value();
            
            if (isPlanNode(nodeName, node)) {
                Plan plan = createPlan(nodeName, node, specificationDirectory);
                plans.put(plan.name(), plan);
                planToTasks.put(plan.name(), new HashSet<>());
                planToUpstreamTasks.put(plan.name(), new HashSet<>());
            } else if (isTaskNode(nodeName, node)) {
                TaskMetadata metadata = createTaskMetadata(nodeName, node, specificationDirectory);
                taskMetadata.put(metadata.name(), metadata);
            } else {
                throw GraphParsingException.parsingError(dotFile.getFileName().toString(), 
                    "Unknown node type: " + nodeName);
            }
        }
        
        // Process edges to establish relationships
        for (MutableNode node : dotGraph.nodes()) {
            String nodeName = node.name().value();
            logger.debug("Processing node: {}", nodeName);
            
            // Get outgoing edges from this node
            for (var link : node.links()) {
                String targetName = link.to().name().value();
                
                // Use the node names directly as IDs
                String sourceId = nodeName;
                String targetId = targetName;
                
                if (plans.containsKey(sourceId) && taskMetadata.containsKey(targetId)) {
                    // Plan -> Task edge
                    logger.debug("Processing plan -> task edge: {} -> {}", sourceId, targetId);
                    planToTasks.get(sourceId).add(targetId);
                    taskToPlan.put(targetId, sourceId);
                    logger.debug("Updated taskToPlan: {} -> {}", targetId, sourceId);
                } else if (taskMetadata.containsKey(sourceId) && plans.containsKey(targetId)) {
                    // Task -> Plan edge
                    logger.debug("Processing task -> plan edge: {} -> {}", sourceId, targetId);
                    planToUpstreamTasks.get(targetId).add(sourceId);
                    logger.debug("Updated planToUpstreamTasks: {} -> {}", targetId, sourceId);
                } else {
                    throw GraphValidationException.invalidGraph(
                        GraphValidationException.ViolationType.INVALID_STRUCTURE,
                        nodeName,
                        String.format("Invalid edge from %s to %s: edges must connect plans to tasks or tasks to plans", 
                        nodeName, targetName));
                }
            }
        }
        
        // Update plans with their upstream task IDs
        Map<String, Plan> updatedPlans = new HashMap<>();
        for (Map.Entry<String, Plan> entry : plans.entrySet()) {
            String planName = entry.getKey();
            Plan plan = entry.getValue();
            Set<String> upstreamTaskIds = planToUpstreamTasks.get(planName);
            
            if (!upstreamTaskIds.isEmpty()) {
                Plan updatedPlan = plan.withUpstreamTasks(upstreamTaskIds);
                updatedPlans.put(planName, updatedPlan);
                logger.debug("Updated plan: {} with upstream tasks: {}", planName, upstreamTaskIds);
            } else {
                updatedPlans.put(planName, plan);
            }
        }
        
        // Create Task objects with known upstream plan IDs
        Map<String, Task> tasks = new HashMap<>();
        for (TaskMetadata metadata : taskMetadata.values()) {
            String upstreamPlan = taskToPlan.get(metadata.name());
            if (upstreamPlan == null) {
                throw GraphValidationException.invalidGraph(
                    GraphValidationException.ViolationType.INVALID_STRUCTURE,
                    metadata.name(),
                    String.format("Task %s has no upstream plan", metadata.name()));
            }
            
            Task task = new Task(metadata.name(), metadata.label(), metadata.taskSource(), upstreamPlan, java.util.List.of());
            tasks.put(task.name(), task);
            logger.debug("Created task: {} with upstream plan: {}", task.name(), upstreamPlan);
        }
        
        // Create the agent graph with the extracted name
        AgentGraph agentGraph = AgentGraph.of(graphName, updatedPlans, tasks, planToTasks, taskToPlan);
        
        // Validate the graph structure
        GraphValidator.validate(agentGraph);
        
        logger.info("Successfully parsed agent graph '{}' with {} plans and {} tasks", 
            graphName, agentGraph.planCount(), agentGraph.taskCount());
        
        return agentGraph;
    }
    
    @Override
    public boolean supports(Path specificationFile) {
        return specificationFile != null && specificationFile.toString().toLowerCase().endsWith(".dot");
    }
    
    @Override
    public String getName() {
        return "GraphViz DOT Parser";
    }
    
    @Override
    public String[] getSupportedExtensions() {
        return new String[]{".dot"};
    }
    
    private Path findDotFile(Path specificationDirectory) throws GraphParsingException {
        try (Stream<Path> paths = Files.walk(specificationDirectory, 1)) {
            return paths
                .filter(Files::isRegularFile)
                .filter(path -> path.toString().toLowerCase().endsWith(".dot"))
                .findFirst()
                .orElseThrow(() -> GraphParsingException.parsingError(
                    specificationDirectory.getFileName().toString(),
                    "No DOT file found in directory"));
        } catch (IOException e) {
            throw GraphParsingException.parsingError(
                specificationDirectory.getFileName().toString(),
                "Error searching for DOT file: " + e.getMessage(), e);
        }
    }
    
    private MutableGraph parseDotFile(Path dotFile) throws GraphParsingException {
        try {
            String dotContent = Files.readString(dotFile);
            return new Parser().read(dotContent);
        } catch (IOException e) {
            throw GraphParsingException.parsingError(dotFile.getFileName().toString(), 
                "Error reading DOT file: " + e.getMessage(), e);
        } catch (Exception e) {
            throw GraphParsingException.parsingError(dotFile.getFileName().toString(), 
                "Error parsing DOT file: " + e.getMessage(), e);
        }
    }
    
    private boolean isPlanNode(String nodeName, MutableNode node) {
        // Check if node has explicit type="plan" attribute
        return node.get("type") != null && "plan".equals(node.get("type"));
    }
    
    private boolean isTaskNode(String nodeName, MutableNode node) {
        // Check if node has explicit type="task" attribute
        return node.get("type") != null && "task".equals(node.get("type"));
    }
    
    private Plan createPlan(String planName, MutableNode node, Path specificationDirectory) throws GraphValidationException {
        // Validate plan name
        if (!isValidIdentifier(planName)) {
            throw GraphValidationException.invalidGraph(
                GraphValidationException.ViolationType.INVALID_NAME,
                planName,
                String.format("Invalid plan name: %s (must be a valid identifier)", planName));
        }
        
        // Get the label from the node, fallback to planName if not present
        Object labelObj = node.get("label");
        String label = labelObj != null ? labelObj.toString() : planName;
        
        // Construct the plan directory path
        Path planDir = specificationDirectory.resolve(PLANS_DIR).resolve(planName);
        
        return new Plan(planName, label, planDir, new java.util.HashSet<>(), java.util.List.of());
    }
    
    private TaskMetadata createTaskMetadata(String taskName, MutableNode node, Path specificationDirectory) throws GraphValidationException {
        // Validate task name
        if (!isValidIdentifier(taskName)) {
            throw GraphValidationException.invalidGraph(
                GraphValidationException.ViolationType.INVALID_NAME,
                taskName,
                String.format("Invalid task name: %s (must be a valid identifier)", taskName));
        }
        
        // Get the label from the node, fallback to taskName if not present
        Object labelObj = node.get("label");
        String label = labelObj != null ? labelObj.toString() : taskName;
        
        // Construct the task directory path
        Path taskDir = specificationDirectory.resolve(TASKS_DIR).resolve(taskName);
        
        // Return metadata without upstream plan ID - this will be determined later
        return new TaskMetadata(taskName, taskDir, label);
    }
    

    
    private boolean isValidIdentifier(String name) {
        return name != null && name.matches("^[a-zA-Z_][a-zA-Z0-9_]*$");
    }
    
    /**
     * Extracts the graph name from the MutableGraph.
     * 
     * @param dotGraph The parsed DOT graph
     * @return The graph name
     * @throws GraphParsingException if the graph name cannot be extracted
     */
    private String extractGraphName(MutableGraph dotGraph, String filename) throws GraphParsingException {
        // Try to get the graph name from the graph object
        if (dotGraph.name() != null && !dotGraph.name().value().isEmpty()) {
            return dotGraph.name().value();
        }
        
        // If no name is found, the DOT file is malformed
        throw GraphParsingException.parsingError(
            filename,
            "Graph name is missing or empty. DOT files must specify a graph name in the format 'digraph GraphName {'");
    }
} 