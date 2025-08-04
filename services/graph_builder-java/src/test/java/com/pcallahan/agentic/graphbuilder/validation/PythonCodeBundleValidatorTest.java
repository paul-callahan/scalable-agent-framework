package com.pcallahan.agentic.graphbuilder.validation;

import com.pcallahan.agentic.graph.model.AgentGraph;
import com.pcallahan.agentic.graph.model.Plan;
import com.pcallahan.agentic.graph.model.Task;
import com.pcallahan.agentic.graph.exception.GraphValidationException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class PythonCodeBundleValidatorTest {
    
    @TempDir
    Path tempDir;
    
    private Path specificationDirectory;
    
    @BeforeEach
    void setUp() throws Exception {
        specificationDirectory = tempDir.resolve("spec");
        Files.createDirectories(specificationDirectory);
    }
    
    @Test
    void testValidateValidGraph() throws Exception {
        // Given
        AgentGraph graph = createValidGraph();
        createValidFileStructure();
        
        // When & Then - should not throw exception
        PythonCodeBundleValidator.validate(graph, specificationDirectory);
    }
    
    @Test
    void testValidateMissingPlanDirectory() throws Exception {
        // Given
        AgentGraph graph = createValidGraph();
        // Don't create file structure
        
        // When & Then
        assertThatThrownBy(() -> PythonCodeBundleValidator.validate(graph, specificationDirectory))
            .isInstanceOf(GraphValidationException.class)
            .hasMessageContaining("Plan directory does not exist");
    }
    
    @Test
    void testValidateMissingTaskDirectory() throws Exception {
        // Given
        AgentGraph graph = createValidGraph();
        createPlansOnly();
        
        // When & Then
        assertThatThrownBy(() -> PythonCodeBundleValidator.validate(graph, specificationDirectory))
            .isInstanceOf(GraphValidationException.class)
            .hasMessageContaining("Task directory does not exist");
    }
    
    @Test
    void testValidateMissingPlanPythonFile() throws Exception {
        // Given
        AgentGraph graph = createValidGraph();
        createFileStructureWithoutPlanPython();
        
        // When & Then
        assertThatThrownBy(() -> PythonCodeBundleValidator.validate(graph, specificationDirectory))
            .isInstanceOf(GraphValidationException.class)
            .hasMessageContaining("Plan Python file not found");
    }
    
    @Test
    void testValidateMissingTaskPythonFile() throws Exception {
        // Given
        AgentGraph graph = createValidGraph();
        createFileStructureWithoutTaskPython();
        
        // When & Then
        assertThatThrownBy(() -> PythonCodeBundleValidator.validate(graph, specificationDirectory))
            .isInstanceOf(GraphValidationException.class)
            .hasMessageContaining("Task Python file not found");
    }
    
    @Test
    void testValidateMissingPlanRequirements() throws Exception {
        // Given
        AgentGraph graph = createValidGraph();
        createFileStructureWithoutPlanRequirements();
        
        // When & Then
        assertThatThrownBy(() -> PythonCodeBundleValidator.validate(graph, specificationDirectory))
            .isInstanceOf(GraphValidationException.class)
            .hasMessageContaining("Plan requirements file not found");
    }
    
    @Test
    void testValidateMissingTaskRequirements() throws Exception {
        // Given
        AgentGraph graph = createValidGraph();
        createFileStructureWithoutTaskRequirements();
        
        // When & Then
        assertThatThrownBy(() -> PythonCodeBundleValidator.validate(graph, specificationDirectory))
            .isInstanceOf(GraphValidationException.class)
            .hasMessageContaining("Task requirements file not found");
    }
    
    private AgentGraph createValidGraph() {
        Map<String, Plan> plans = new HashMap<>();
        Map<String, Task> tasks = new HashMap<>();
        
        // Create a plan
        Plan plan = new Plan("plan_data_collection", "Data Collection Plan", 
            specificationDirectory.resolve("plans").resolve("plan_data_collection"), new HashSet<>());
        plans.put("plan_data_collection", plan);
        
        // Create a task
        Task task = new Task("task_fetch_data", "Fetch Data", 
            specificationDirectory.resolve("tasks").resolve("task_fetch_data"), "plan_data_collection");
        tasks.put("task_fetch_data", task);
        
        return AgentGraph.of(plans, tasks, new HashMap<>(), new HashMap<>());
    }
    
    private void createValidFileStructure() throws Exception {
        // Create plans directory
        Path plansDir = specificationDirectory.resolve("plans");
        Files.createDirectories(plansDir);
        
        // Create plan directory with files
        Path planDir = plansDir.resolve("plan_data_collection");
        Files.createDirectories(planDir);
        Files.write(planDir.resolve("plan.py"), "def plan(): pass".getBytes());
        Files.write(planDir.resolve("requirements.txt"), "requests".getBytes());
        
        // Create tasks directory
        Path tasksDir = specificationDirectory.resolve("tasks");
        Files.createDirectories(tasksDir);
        
        // Create task directory with files
        Path taskDir = tasksDir.resolve("task_fetch_data");
        Files.createDirectories(taskDir);
        Files.write(taskDir.resolve("task.py"), "def task(): pass".getBytes());
        Files.write(taskDir.resolve("requirements.txt"), "pandas".getBytes());
    }
    
    private void createPlansOnly() throws Exception {
        // Create plans directory only
        Path plansDir = specificationDirectory.resolve("plans");
        Files.createDirectories(plansDir);
        
        Path planDir = plansDir.resolve("plan_data_collection");
        Files.createDirectories(planDir);
        Files.write(planDir.resolve("plan.py"), "def plan(): pass".getBytes());
        Files.write(planDir.resolve("requirements.txt"), "requests".getBytes());
    }
    
    private void createFileStructureWithoutPlanPython() throws Exception {
        // Create plans directory without plan.py
        Path plansDir = specificationDirectory.resolve("plans");
        Files.createDirectories(plansDir);
        
        Path planDir = plansDir.resolve("plan_data_collection");
        Files.createDirectories(planDir);
        Files.write(planDir.resolve("requirements.txt"), "requests".getBytes());
        
        // Create tasks directory
        Path tasksDir = specificationDirectory.resolve("tasks");
        Files.createDirectories(tasksDir);
        
        Path taskDir = tasksDir.resolve("task_fetch_data");
        Files.createDirectories(taskDir);
        Files.write(taskDir.resolve("task.py"), "def task(): pass".getBytes());
        Files.write(taskDir.resolve("requirements.txt"), "pandas".getBytes());
    }
    
    private void createFileStructureWithoutTaskPython() throws Exception {
        // Create plans directory
        Path plansDir = specificationDirectory.resolve("plans");
        Files.createDirectories(plansDir);
        
        Path planDir = plansDir.resolve("plan_data_collection");
        Files.createDirectories(planDir);
        Files.write(planDir.resolve("plan.py"), "def plan(): pass".getBytes());
        Files.write(planDir.resolve("requirements.txt"), "requests".getBytes());
        
        // Create tasks directory without task.py
        Path tasksDir = specificationDirectory.resolve("tasks");
        Files.createDirectories(tasksDir);
        
        Path taskDir = tasksDir.resolve("task_fetch_data");
        Files.createDirectories(taskDir);
        Files.write(taskDir.resolve("requirements.txt"), "pandas".getBytes());
    }
    
    private void createFileStructureWithoutPlanRequirements() throws Exception {
        // Create plans directory without requirements.txt
        Path plansDir = specificationDirectory.resolve("plans");
        Files.createDirectories(plansDir);
        
        Path planDir = plansDir.resolve("plan_data_collection");
        Files.createDirectories(planDir);
        Files.write(planDir.resolve("plan.py"), "def plan(): pass".getBytes());
        
        // Create tasks directory
        Path tasksDir = specificationDirectory.resolve("tasks");
        Files.createDirectories(tasksDir);
        
        Path taskDir = tasksDir.resolve("task_fetch_data");
        Files.createDirectories(taskDir);
        Files.write(taskDir.resolve("task.py"), "def task(): pass".getBytes());
        Files.write(taskDir.resolve("requirements.txt"), "pandas".getBytes());
    }
    
    private void createFileStructureWithoutTaskRequirements() throws Exception {
        // Create plans directory
        Path plansDir = specificationDirectory.resolve("plans");
        Files.createDirectories(plansDir);
        
        Path planDir = plansDir.resolve("plan_data_collection");
        Files.createDirectories(planDir);
        Files.write(planDir.resolve("plan.py"), "def plan(): pass".getBytes());
        Files.write(planDir.resolve("requirements.txt"), "requests".getBytes());
        
        // Create tasks directory without requirements.txt
        Path tasksDir = specificationDirectory.resolve("tasks");
        Files.createDirectories(tasksDir);
        
        Path taskDir = tasksDir.resolve("task_fetch_data");
        Files.createDirectories(taskDir);
        Files.write(taskDir.resolve("task.py"), "def task(): pass".getBytes());
    }
} 