package com.pcallahan.agentic.graphbuilder;

import com.pcallahan.agentic.common.graph.AgentGraph;
import com.pcallahan.agentic.common.graph.Plan;
import com.pcallahan.agentic.common.graph.Task;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class GraphvizGraphParserTest {

    @Test
    void parsesValidGraph() throws Exception {
        String dot = "digraph{\n" +
                "plan1 [type=\"plan\" plan_source=\"plans/plan1\"]\n" +
                "plan2 [type=\"plan\" plan_source=\"plans/plan2\"]\n" +
                "task1 [type=\"task\" task_source=\"tasks/task1\"]\n" +
                "task2 [type=\"task\" task_source=\"tasks/task2\"]\n" +
                "plan1 -> task1\n" +
                "plan1 -> task2\n" +
                "task1 -> plan2\n" +
                "task2 -> plan2\n" +
                "}";
        Path tmp = Files.createTempFile("graph", ".dot");
        Files.writeString(tmp, dot);

        GraphParser parser = new GraphvizGraphParser();
        AgentGraph graph = parser.parse(tmp);

        assertEquals(2, graph.getPlans().size());
        assertEquals(2, graph.getTasks().size());
        assertEquals(List.of("task1", "task2"), graph.getPlanToTasks().get("plan1"));
        assertEquals("plan1", graph.getTaskToPlan().get("task1"));

        Plan plan2 = graph.getPlans().stream().filter(p -> p.name().equals("plan2")).findFirst().orElseThrow();
        assertEquals(List.of("task1", "task2"), plan2.upstreamTaskIds());
    }

    @Test
    void failsOnUnconnectedPlan() throws Exception {
        String dot = "digraph{ plan1 [type=\"plan\" plan_source=\"plans/p1\"] }";
        Path tmp = Files.createTempFile("bad", ".dot");
        Files.writeString(tmp, dot);

        GraphParser parser = new GraphvizGraphParser();
        assertThrows(GraphParseException.class, () -> parser.parse(tmp));
    }
}
