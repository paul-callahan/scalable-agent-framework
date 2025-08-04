package com.pcallahan.agentic.graph.model;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class PlanTest {
    
    @TempDir
    Path tempDir;
    
    private Path testPlanPath;
    
    @BeforeEach
    void setUp() {
        testPlanPath = tempDir.resolve("test_plan");
    }
    
    @Test
    void testValidConstruction() {
        // Given & When
        Plan plan = Plan.of("test_plan", testPlanPath);
        
        // Then
        assertThat(plan.name()).isEqualTo("test_plan");
        assertThat(plan.planSource()).isEqualTo(testPlanPath);
        assertThat(plan.upstreamTaskIds()).isEmpty();
    }
    
    @Test
    void testConstructionWithUpstreamTasks() {
        // Given
        Set<String> upstreamTasks = Set.of("task1", "task2");
        
        // When
        Plan plan = Plan.of("test_plan", testPlanPath, upstreamTasks);
        
        // Then
        assertThat(plan.name()).isEqualTo("test_plan");
        assertThat(plan.planSource()).isEqualTo(testPlanPath);
        assertThat(plan.upstreamTaskIds()).containsExactlyInAnyOrder("task1", "task2");
    }
    
    @Test
    void testValidationInConstructor() {
        // Given & When & Then
        assertThatThrownBy(() -> Plan.of(null, testPlanPath))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Plan name cannot be null or empty");
        
        assertThatThrownBy(() -> Plan.of("", testPlanPath))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Plan name cannot be null or empty");
        
        assertThatThrownBy(() -> Plan.of("   ", testPlanPath))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Plan name cannot be null or empty");
        
        assertThatThrownBy(() -> Plan.of("test_plan", null))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("Plan source cannot be null");
    }
    
    @Test
    void testImmutability() {
        // Given
        Set<String> upstreamTasks = Set.of("task1", "task2");
        Plan plan = Plan.of("test_plan", testPlanPath, upstreamTasks);
        
        // When & Then
        assertThatThrownBy(() -> plan.upstreamTaskIds().add("task3"))
            .isInstanceOf(UnsupportedOperationException.class);
    }
    
    @Test
    void testWithUpstreamTask() {
        // Given
        Plan plan = Plan.of("test_plan", testPlanPath);
        
        // When
        Plan newPlan = plan.withUpstreamTask("task1");
        
        // Then
        assertThat(newPlan.name()).isEqualTo("test_plan");
        assertThat(newPlan.planSource()).isEqualTo(testPlanPath);
        assertThat(newPlan.upstreamTaskIds()).containsExactly("task1");
        
        // Original plan should be unchanged
        assertThat(plan.upstreamTaskIds()).isEmpty();
    }
    
    @Test
    void testWithUpstreamTasks() {
        // Given
        Plan plan = Plan.of("test_plan", testPlanPath);
        Set<String> newUpstreamTasks = Set.of("task1", "task2", "task3");
        
        // When
        Plan newPlan = plan.withUpstreamTasks(newUpstreamTasks);
        
        // Then
        assertThat(newPlan.name()).isEqualTo("test_plan");
        assertThat(newPlan.planSource()).isEqualTo(testPlanPath);
        assertThat(newPlan.upstreamTaskIds()).containsExactlyInAnyOrder("task1", "task2", "task3");
        
        // Original plan should be unchanged
        assertThat(plan.upstreamTaskIds()).isEmpty();
    }
    
    @Test
    void testEqualsAndHashCode() {
        // Given
        Plan plan1 = Plan.of("test_plan", testPlanPath);
        Plan plan2 = Plan.of("test_plan", testPlanPath);
        Plan plan3 = Plan.of("different_plan", testPlanPath);
        
        // When & Then
        assertThat(plan1).isEqualTo(plan2);
        assertThat(plan1).isNotEqualTo(plan3);
        assertThat(plan1.hashCode()).isEqualTo(plan2.hashCode());
        assertThat(plan1.hashCode()).isNotEqualTo(plan3.hashCode());
    }
    
    @Test
    void testNullUpstreamTaskIds() {
        // Given & When
        Plan plan = new Plan("test_plan", "test_plan", testPlanPath, null);
        
        // Then
        assertThat(plan.upstreamTaskIds()).isEmpty();
    }
} 