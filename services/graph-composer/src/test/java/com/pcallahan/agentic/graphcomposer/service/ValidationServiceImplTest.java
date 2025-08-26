package com.pcallahan.agentic.graphcomposer.service;

import com.pcallahan.agentic.graphcomposer.dto.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class ValidationServiceImplTest {

    @InjectMocks
    private ValidationServiceImpl validationService;

    private AgentGraphDto testGraph;
    private PlanDto testPlan;
    private TaskDto testTask;

    @BeforeEach
    void setUp() {
        testPlan = new PlanDto();
        testPlan.setName("test_plan");
        testPlan.setLabel("Test Plan");
        testPlan.setUpstreamTaskIds(Set.of("test_task"));

        testTask = new TaskDto();
        testTask.setName("test_task");
        testTask.setLabel("Test Task");
        testTask.setUpstreamPlanId("test_plan");

        testGraph = new AgentGraphDto();
        testGraph.setName("Test Graph");
        testGraph.setTenantId("test-tenant");
        testGraph.setPlans(List.of(testPlan));
        testGraph.setTasks(List.of(testTask));
        testGraph.setPlanToTasks(Map.of("test_plan", Set.of("test_task")));
        testGraph.setTaskToPlan(Map.of("test_task", "test_plan"));
    }

    @Test
    void validateGraph_ShouldReturnValid_WhenGraphIsCorrect() {
        // When
        ValidationResult result = validationService.validateGraph(testGraph);

        // Then
        assertTrue(result.isValid());
        assertTrue(result.getErrors().isEmpty());
    }

    @Test
    void validateGraph_ShouldReturnInvalid_WhenGraphIsNull() {
        // When
        ValidationResult result = validationService.validateGraph(null);

        // Then
        assertFalse(result.isValid());
        assertEquals(1, result.getErrors().size());
        assertEquals("Graph cannot be null", result.getErrors().get(0));
    }

    @Test
    void validateGraph_ShouldReturnInvalid_WhenNameIsEmpty() {
        // Given
        testGraph.setName("");

        // When
        ValidationResult result = validationService.validateGraph(testGraph);

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Graph name cannot be empty"));
    }

    @Test
    void validateGraph_ShouldReturnInvalid_WhenTenantIdIsEmpty() {
        // Given
        testGraph.setTenantId("");

        // When
        ValidationResult result = validationService.validateGraph(testGraph);

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Tenant ID cannot be empty"));
    }

    @Test
    void validateNodeName_ShouldReturnValid_WhenNameIsValidPythonIdentifier() {
        // Given
        NodeNameValidationRequest request = new NodeNameValidationRequest();
        request.setNodeName("valid_node_name");
        request.setGraphId("test-graph");

        // When
        ValidationResult result = validationService.validateNodeName(request);

        // Then
        assertTrue(result.isValid());
        assertTrue(result.getErrors().isEmpty());
    }

    @Test
    void validateNodeName_ShouldReturnInvalid_WhenNameIsEmpty() {
        // Given
        NodeNameValidationRequest request = new NodeNameValidationRequest();
        request.setNodeName("");
        request.setGraphId("test-graph");

        // When
        ValidationResult result = validationService.validateNodeName(request);

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Node name cannot be empty"));
    }

    @Test
    void validateNodeName_ShouldReturnInvalid_WhenNameAlreadyExists() {
        // Given
        NodeNameValidationRequest request = new NodeNameValidationRequest();
        request.setNodeName("existing_node");
        request.setGraphId("test-graph");
        request.setExistingNodeNames(Set.of("existing_node", "other_node"));

        // When
        ValidationResult result = validationService.validateNodeName(request);

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Node name 'existing_node' already exists in the graph"));
    }

    @Test
    void validateConnectionConstraints_ShouldReturnValid_WhenConnectionsAreCorrect() {
        // When
        ValidationResult result = validationService.validateConnectionConstraints(testGraph);

        // Then
        assertTrue(result.isValid());
        assertTrue(result.getErrors().isEmpty());
    }

    @Test
    void validateConnectionConstraints_ShouldReturnInvalid_WhenPlanConnectsToNonTask() {
        // Given
        testGraph.setPlanToTasks(Map.of("test_plan", Set.of("non_existent_task")));

        // When
        ValidationResult result = validationService.validateConnectionConstraints(testGraph);

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Plan 'test_plan' is connected to 'non_existent_task' which is not a task"));
    }

    @Test
    void validateConnectionConstraints_ShouldReturnInvalid_WhenTaskConnectsToNonPlan() {
        // Given
        testGraph.setTaskToPlan(Map.of("test_task", "non_existent_plan"));

        // When
        ValidationResult result = validationService.validateConnectionConstraints(testGraph);

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Task 'test_task' is connected to 'non_existent_plan' which is not a plan"));
    }

    @Test
    void validateTaskUpstreamConstraints_ShouldReturnValid_WhenTaskHasOneUpstreamPlan() {
        // When
        ValidationResult result = validationService.validateTaskUpstreamConstraints(testGraph);

        // Then
        assertTrue(result.isValid());
        assertTrue(result.getErrors().isEmpty());
    }

    @Test
    void validateTaskUpstreamConstraints_ShouldReturnInvalid_WhenTaskHasNoUpstreamPlan() {
        // Given
        testGraph.setTaskToPlan(Map.of());

        // When
        ValidationResult result = validationService.validateTaskUpstreamConstraints(testGraph);

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Task 'test_task' must have exactly one upstream plan"));
    }

    @Test
    void validatePlanUpstreamConstraints_ShouldReturnValid_WhenPlanHasValidUpstreamTasks() {
        // When
        ValidationResult result = validationService.validatePlanUpstreamConstraints(testGraph);

        // Then
        assertTrue(result.isValid());
        assertTrue(result.getErrors().isEmpty());
    }

    @Test
    void validatePlanUpstreamConstraints_ShouldReturnInvalid_WhenPlanReferencesNonExistentTask() {
        // Given
        testPlan.setUpstreamTaskIds(Set.of("non_existent_task"));

        // When
        ValidationResult result = validationService.validatePlanUpstreamConstraints(testGraph);

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Plan 'test_plan' references upstream task 'non_existent_task' which does not exist"));
    }

    @Test
    void validateConnectivity_ShouldReturnWarning_WhenNodeIsOrphaned() {
        // Given
        PlanDto orphanedPlan = new PlanDto();
        orphanedPlan.setName("orphaned_plan");
        orphanedPlan.setLabel("Orphaned Plan");
        
        testGraph.setPlans(List.of(testPlan, orphanedPlan));

        // When
        ValidationResult result = validationService.validateConnectivity(testGraph);

        // Then
        assertTrue(result.isValid()); // Warnings don't make it invalid
        assertTrue(result.getWarnings().contains("Node 'orphaned_plan' is not connected to any other nodes"));
    }

    @Test
    void validateConnectivity_ShouldReturnWarning_WhenGraphIsEmpty() {
        // Given
        testGraph.setPlans(List.of());
        testGraph.setTasks(List.of());

        // When
        ValidationResult result = validationService.validateConnectivity(testGraph);

        // Then
        assertTrue(result.isValid()); // Warnings don't make it invalid
        assertTrue(result.getWarnings().contains("Graph contains no nodes"));
    }

    @Test
    void validateNodeNameUniqueness_ShouldReturnValid_WhenAllNamesAreUnique() {
        // When
        ValidationResult result = validationService.validateNodeNameUniqueness(testGraph);

        // Then
        assertTrue(result.isValid());
        assertTrue(result.getErrors().isEmpty());
    }

    @Test
    void validateNodeNameUniqueness_ShouldReturnInvalid_WhenNamesAreDuplicated() {
        // Given
        TaskDto duplicateTask = new TaskDto();
        duplicateTask.setName("test_plan"); // Same name as the plan
        duplicateTask.setLabel("Duplicate Task");
        
        testGraph.setTasks(List.of(testTask, duplicateTask));

        // When
        ValidationResult result = validationService.validateNodeNameUniqueness(testGraph);

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Node name 'test_plan' is used multiple times in the graph"));
    }

    @Test
    void validatePythonIdentifier_ShouldReturnValid_WhenNameIsValidIdentifier() {
        // When
        ValidationResult result = validationService.validatePythonIdentifier("valid_identifier");

        // Then
        assertTrue(result.isValid());
        assertTrue(result.getErrors().isEmpty());
    }

    @Test
    void validatePythonIdentifier_ShouldReturnInvalid_WhenNameStartsWithDigit() {
        // When
        ValidationResult result = validationService.validatePythonIdentifier("123invalid");

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().get(0).contains("not a valid Python identifier"));
    }

    @Test
    void validatePythonIdentifier_ShouldReturnInvalid_WhenNameIsPythonKeyword() {
        // When
        ValidationResult result = validationService.validatePythonIdentifier("def");

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Node name 'def' is a Python keyword and cannot be used as an identifier"));
    }

    @Test
    void validatePythonIdentifier_ShouldReturnWarning_WhenNameStartsWithUnderscore() {
        // When
        ValidationResult result = validationService.validatePythonIdentifier("_private_name");

        // Then
        assertTrue(result.isValid());
        assertTrue(result.getWarnings().contains("Node name '_private_name' starts with underscore, which is typically reserved for internal use"));
    }

    @Test
    void validatePythonIdentifier_ShouldReturnWarning_WhenNameIsAllUppercase() {
        // When
        ValidationResult result = validationService.validatePythonIdentifier("CONSTANT_NAME");

        // Then
        assertTrue(result.isValid());
        assertTrue(result.getWarnings().contains("Node name 'CONSTANT_NAME' is all uppercase, which is typically reserved for constants"));
    }

    @Test
    void validatePythonIdentifier_ShouldReturnInvalid_WhenNameIsEmpty() {
        // When
        ValidationResult result = validationService.validatePythonIdentifier("");

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().contains("Node name cannot be empty"));
    }

    @Test
    void validatePythonIdentifier_ShouldReturnInvalid_WhenNameContainsSpecialCharacters() {
        // When
        ValidationResult result = validationService.validatePythonIdentifier("invalid-name");

        // Then
        assertFalse(result.isValid());
        assertTrue(result.getErrors().get(0).contains("not a valid Python identifier"));
    }
}