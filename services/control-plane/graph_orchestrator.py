from dataclasses import dataclass
from typing import Dict, Any, List
from ..standalone_py.agent_lifetime import AgentLifetime
from ..standalone_py.agent_graph import AgentGraph


@dataclass
class GraphOrchestrator:
    """Manages AgentLifetime execution flow"""
    
    def __init__(self):
        """Initialize the graph orchestrator"""
        self.active_lifetimes: Dict[str, AgentLifetime] = {}
        self.graph_templates: Dict[str, AgentGraph] = {}
    
    def start_lifetime(self, graph_id: str, tenant_id: str, input_data: str) -> str:
        """Start a new agent lifetime"""
        if graph_id not in self.graph_templates:
            raise ValueError(f"Graph template {graph_id} not found")
        
        graph = self.graph_templates[graph_id]
        lifetime_id = f"lifetime_{tenant_id}_{graph_id}_{len(self.active_lifetimes)}"
        
        # Create new lifetime
        lifetime = AgentLifetime(
            lifetime_id=lifetime_id,
            graph_id=graph_id,
            graph_version=graph.version,
            status="RUNNING",
            started_at=None,  # Would use actual timestamp
            ended_at=None,
            input_data=input_data,
            output_data=None,
            metadata={},
            tenant_id=tenant_id
        )
        
        self.active_lifetimes[lifetime_id] = lifetime
        return lifetime_id
    
    def register_graph_template(self, graph: AgentGraph) -> None:
        """Register a graph template"""
        self.graph_templates[graph.graph_id] = graph
    
    def get_lifetime(self, lifetime_id: str) -> AgentLifetime:
        """Get an active lifetime"""
        if lifetime_id not in self.active_lifetimes:
            raise ValueError(f"Lifetime {lifetime_id} not found")
        return self.active_lifetimes[lifetime_id]
    
    def update_lifetime_status(self, lifetime_id: str, status: str) -> None:
        """Update lifetime status"""
        if lifetime_id in self.active_lifetimes:
            self.active_lifetimes[lifetime_id].status = status 