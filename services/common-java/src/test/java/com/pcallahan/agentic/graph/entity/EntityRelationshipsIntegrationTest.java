package com.pcallahan.agentic.graph.entity;

import com.pcallahan.agentic.graph.repository.AgentGraphRepository;
import com.pcallahan.agentic.graph.repository.ExecutorFileRepository;
import com.pcallahan.agentic.graph.repository.PlanRepository;
import com.pcallahan.agentic.graph.repository.TaskRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;


import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Integration tests for entity relationships using TestContainers.
 */
@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class EntityRelationshipsIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
            .withDatabaseName("test_entity_relationships")
            .withUsername("test")
            .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "create-drop");
    }



    @Autowired
    private AgentGraphRepository agentGraphRepository;

    @Autowired
    private PlanRepository planRepository;

    @Autowired
    private TaskRepository taskRepository;

    @Autowired
    private ExecutorFileRepository executorFileRepository;

    private AgentGraphEntity testGraph;

    @BeforeEach
    void setUp() {
        testGraph = new AgentGraphEntity(
                UUID.randomUUID().toString(),
                "test-tenant",
                "test-graph",
                GraphStatus.NEW
        );
        testGraph = agentGraphRepository.saveAndFlush(testGraph);
    }

    @Test
    void shouldCreateAgentGraphWithStatus() {
        // When
        AgentGraphEntity found = agentGraphRepository.findById(testGraph.getId()).orElse(null);

        // Then
        assertThat(found).isNotNull();
        assertThat(found.getStatus()).isEqualTo(GraphStatus.NEW);
        assertThat(found.getTenantId()).isEqualTo("test-tenant");
        assertThat(found.getName()).isEqualTo("test-graph");
        assertThat(found.getCreatedAt()).isNotNull();
        assertThat(found.getUpdatedAt()).isNotNull();
    }

    @Test
    void shouldCreatePlanWithExecutorFiles() {
        // Given
        PlanEntity plan = new PlanEntity(
                UUID.randomUUID().toString(),
                "data-collection",
                "Data Collection Plan",
                "/plans/data-collection",
                testGraph
        );
        final PlanEntity savedPlan = planRepository.save(plan);

        ExecutorFileEntity planFile = new ExecutorFileEntity(
                UUID.randomUUID().toString(),
                "plan.py",
                "def plan(input): return result",
                "1.0",
                savedPlan
        );
        ExecutorFileEntity requirementsFile = new ExecutorFileEntity(
                UUID.randomUUID().toString(),
                "requirements.txt",
                "requests==2.28.1\nnumpy==1.24.0",
                "1.0",
                savedPlan
        );

        executorFileRepository.save(planFile);
        executorFileRepository.save(requirementsFile);

        // When
        List<ExecutorFileEntity> files = executorFileRepository.findByPlanId(savedPlan.getId());

        // Then
        assertThat(files).hasSize(2);
        assertThat(files).extracting(ExecutorFileEntity::getName)
                .containsExactlyInAnyOrder("plan.py", "requirements.txt");
        
        // Verify bidirectional relationship
        files.forEach(file -> {
            assertThat(file.getPlan()).isEqualTo(savedPlan);
            assertThat(file.getTask()).isNull();
        });
    }

    @Test
    void shouldCreateTaskWithExecutorFiles() {
        // Given
        PlanEntity plan = new PlanEntity(
                UUID.randomUUID().toString(),
                "data-collection",
                "Data Collection Plan",
                "/plans/data-collection",
                testGraph
        );
        final PlanEntity savedPlan = planRepository.save(plan);

        TaskEntity task = new TaskEntity(
                UUID.randomUUID().toString(),
                "fetch-data",
                "Fetch Data Task",
                "/tasks/fetch-data",
                testGraph,
                savedPlan
        );
        final TaskEntity savedTask = taskRepository.save(task);

        ExecutorFileEntity taskFile = new ExecutorFileEntity(
                UUID.randomUUID().toString(),
                "task.py",
                "def task(input): return result",
                "1.0",
                savedTask
        );
        ExecutorFileEntity requirementsFile = new ExecutorFileEntity(
                UUID.randomUUID().toString(),
                "requirements.txt",
                "pandas==1.5.0\nrequests==2.28.1",
                "1.0",
                savedTask
        );

        executorFileRepository.save(taskFile);
        executorFileRepository.save(requirementsFile);

        // When
        List<ExecutorFileEntity> files = executorFileRepository.findByTaskId(savedTask.getId());

        // Then
        assertThat(files).hasSize(2);
        assertThat(files).extracting(ExecutorFileEntity::getName)
                .containsExactlyInAnyOrder("task.py", "requirements.txt");
        
        // Verify bidirectional relationship
        files.forEach(file -> {
            assertThat(file.getTask()).isEqualTo(savedTask);
            assertThat(file.getPlan()).isNull();
        });
    }

    @Test
    void shouldMaintainPlanTaskRelationships() {
        // Given
        PlanEntity plan = new PlanEntity(
                UUID.randomUUID().toString(),
                "data-collection",
                "Data Collection Plan",
                "/plans/data-collection",
                testGraph
        );
        final PlanEntity savedPlan = planRepository.save(plan);

        TaskEntity task1 = new TaskEntity(
                UUID.randomUUID().toString(),
                "fetch-data",
                "Fetch Data Task",
                "/tasks/fetch-data",
                testGraph,
                savedPlan
        );
        TaskEntity task2 = new TaskEntity(
                UUID.randomUUID().toString(),
                "process-data",
                "Process Data Task",
                "/tasks/process-data",
                testGraph,
                savedPlan
        );
        taskRepository.save(task1);
        taskRepository.save(task2);

        // When
        List<TaskEntity> downstreamTasks = taskRepository.findByUpstreamPlanId(savedPlan.getId());

        // Then
        assertThat(downstreamTasks).hasSize(2);
        assertThat(downstreamTasks).extracting(TaskEntity::getName)
                .containsExactlyInAnyOrder("fetch-data", "process-data");
        
        // Verify upstream relationship
        downstreamTasks.forEach(task -> {
            assertThat(task.getUpstreamPlan()).isEqualTo(savedPlan);
        });
    }

    @Test
    void shouldDeleteFilesByPlanId() {
        // Given
        PlanEntity plan = new PlanEntity(
                UUID.randomUUID().toString(),
                "data-collection",
                "Data Collection Plan",
                "/plans/data-collection",
                testGraph
        );
        plan = planRepository.save(plan);

        ExecutorFileEntity planFile = new ExecutorFileEntity(
                UUID.randomUUID().toString(),
                "plan.py",
                "def plan(input): return result",
                "1.0",
                plan
        );
        executorFileRepository.save(planFile);

        // When
        executorFileRepository.deleteByPlanId(plan.getId());

        // Then
        List<ExecutorFileEntity> remainingFiles = executorFileRepository.findByPlanId(plan.getId());
        assertThat(remainingFiles).isEmpty();
    }

    @Test
    void shouldDeleteFilesByTaskId() {
        // Given
        PlanEntity plan = new PlanEntity(
                UUID.randomUUID().toString(),
                "data-collection",
                "Data Collection Plan",
                "/plans/data-collection",
                testGraph
        );
        plan = planRepository.save(plan);

        TaskEntity task = new TaskEntity(
                UUID.randomUUID().toString(),
                "fetch-data",
                "Fetch Data Task",
                "/tasks/fetch-data",
                testGraph,
                plan
        );
        task = taskRepository.save(task);

        ExecutorFileEntity taskFile = new ExecutorFileEntity(
                UUID.randomUUID().toString(),
                "task.py",
                "def task(input): return result",
                "1.0",
                task
        );
        executorFileRepository.save(taskFile);

        // When
        executorFileRepository.deleteByTaskId(task.getId());

        // Then
        List<ExecutorFileEntity> remainingFiles = executorFileRepository.findByTaskId(task.getId());
        assertThat(remainingFiles).isEmpty();
    }

    @Test
    void shouldFindGraphsByStatus() {
        // Given
        AgentGraphEntity runningGraph = new AgentGraphEntity(
                UUID.randomUUID().toString(),
                "test-tenant",
                "running-graph",
                GraphStatus.RUNNING
        );
        AgentGraphEntity errorGraph = new AgentGraphEntity(
                UUID.randomUUID().toString(),
                "test-tenant",
                "error-graph",
                GraphStatus.ERROR
        );
        agentGraphRepository.save(runningGraph);
        agentGraphRepository.save(errorGraph);

        // When
        List<AgentGraphEntity> newGraphs = agentGraphRepository.findByTenantIdAndStatusOrderByCreatedAtDesc(
                "test-tenant", GraphStatus.NEW);
        List<AgentGraphEntity> runningGraphs = agentGraphRepository.findByTenantIdAndStatusOrderByCreatedAtDesc(
                "test-tenant", GraphStatus.RUNNING);
        List<AgentGraphEntity> errorGraphs = agentGraphRepository.findByTenantIdAndStatusOrderByCreatedAtDesc(
                "test-tenant", GraphStatus.ERROR);

        // Then
        assertThat(newGraphs).hasSize(1);
        assertThat(newGraphs.get(0).getName()).isEqualTo("test-graph");
        
        assertThat(runningGraphs).hasSize(1);
        assertThat(runningGraphs.get(0).getName()).isEqualTo("running-graph");
        
        assertThat(errorGraphs).hasSize(1);
        assertThat(errorGraphs.get(0).getName()).isEqualTo("error-graph");
    }

    @Test
    void shouldCheckFileExistence() {
        // Given
        PlanEntity plan = new PlanEntity(
                UUID.randomUUID().toString(),
                "data-collection",
                "Data Collection Plan",
                "/plans/data-collection",
                testGraph
        );
        plan = planRepository.save(plan);

        ExecutorFileEntity file = new ExecutorFileEntity(
                UUID.randomUUID().toString(),
                "plan.py",
                "def plan(input): return result",
                "1.0",
                plan
        );
        executorFileRepository.save(file);

        // When & Then
        assertThat(executorFileRepository.existsByPlanIdAndName(plan.getId(), "plan.py")).isTrue();
        assertThat(executorFileRepository.existsByPlanIdAndName(plan.getId(), "nonexistent.py")).isFalse();
    }
}