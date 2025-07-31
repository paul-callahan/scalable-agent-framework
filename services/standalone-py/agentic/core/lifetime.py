"""
AgentLifetime class for the agentic framework.

AgentLifetime represents one runtime instance of an AgentGraph executing to completion.
It manages the execution state and provides control operations like pause/resume/abort.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .graph import AgentGraph
from .task import TaskResult
from .plan import PlanResult


class LifetimeStatus(Enum):
    """Status of an AgentLifetime instance."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class AgentLifetime:
    """
    Runtime instance of an AgentGraph execution.
    
    AgentLifetime represents one execution of an AgentGraph from start to completion.
    It manages the execution state, tracks progress, and provides control operations.
    """
    
    def __init__(self, 
                 tenant_id: str,
                 graph: AgentGraph,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new AgentLifetime.
        
        Args:
            tenant_id: Tenant identifier for multi-tenancy
            graph: AgentGraph to execute
            metadata: Optional metadata for the lifetime
        """
        self.tenant_id = tenant_id
        self.graph = graph
        self.metadata = metadata or {}
        self.id = str(uuid.uuid4())
        
        # Execution state
        self.status = LifetimeStatus.PENDING
        self.current_node_ids: Set[str] = set()
        self.completed_node_ids: Set[str] = set()
        self.failed_node_ids: Set[str] = set()
        self.execution_history: List[Dict[str, Any]] = []
        
        # Initialize with start nodes
        self.current_node_ids = set(self.graph.get_start_nodes())
        
        # Timestamps
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Validate tenant_id consistency
        if self.graph.tenant_id != self.tenant_id:
            raise ValueError("Graph tenant_id must match lifetime tenant_id")
    
    def start(self) -> None:
        """
        Start the lifetime execution.
        
        Raises:
            RuntimeError: If already started or completed
        """
        if self.status != LifetimeStatus.PENDING:
            raise RuntimeError(f"Cannot start lifetime in status: {self.status}")
        
        self.status = LifetimeStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def pause(self) -> None:
        """
        Pause the lifetime execution.
        
        Raises:
            RuntimeError: If not running
        """
        if self.status != LifetimeStatus.RUNNING:
            raise RuntimeError(f"Cannot pause lifetime in status: {self.status}")
        
        self.status = LifetimeStatus.PAUSED
    
    def resume(self) -> None:
        """
        Resume the lifetime execution.
        
        Raises:
            RuntimeError: If not paused
        """
        if self.status != LifetimeStatus.PAUSED:
            raise RuntimeError(f"Cannot resume lifetime in status: {self.status}")
        
        self.status = LifetimeStatus.RUNNING
    
    def abort(self, reason: str = "User requested abort") -> None:
        """
        Abort the lifetime execution.
        
        Args:
            reason: Reason for aborting the execution
        """
        self.status = LifetimeStatus.ABORTED
        self.completed_at = datetime.utcnow()
        
        # Record abort in history
        self.execution_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'abort',
            'reason': reason
        })
    
    def complete_node(self, node_id: str, result: Any) -> None:
        """
        Mark a node as completed with its result.
        
        Args:
            node_id: ID of the completed node
            result: Result from the node execution
        """
        if node_id not in self.current_node_ids:
            raise ValueError(f"Node {node_id} is not currently running")
        
        self.current_node_ids.remove(node_id)
        self.completed_node_ids.add(node_id)
        
        # Record completion in history
        self.execution_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'complete_node',
            'node_id': node_id,
            'result': result
        })
        
        # Check if execution is complete
        self._check_completion()
    
    def fail_node(self, node_id: str, error: str) -> None:
        """
        Mark a node as failed.
        
        Args:
            node_id: ID of the failed node
            error: Error message
        """
        if node_id not in self.current_node_ids:
            raise ValueError(f"Node {node_id} is not currently running")
        
        self.current_node_ids.remove(node_id)
        self.failed_node_ids.add(node_id)
        
        # Record failure in history
        self.execution_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'fail_node',
            'node_id': node_id,
            'error': error
        })
        
        # Check if execution should fail
        self._check_completion()
    
    def get_next_nodes(self, completed_node_id: str) -> List[str]:
        """
        Get the next nodes to execute after completing a node.
        
        Args:
            completed_node_id: ID of the node that was just completed
            
        Returns:
            List of node IDs to execute next
        """
        next_nodes = []
        outgoing_edges = self.graph.get_outgoing_edges(completed_node_id)
        
        for edge in outgoing_edges:
            if edge.should_traverse(self._get_context()):
                next_nodes.append(edge.target_id)
        
        return next_nodes
    
    def _get_context(self) -> Dict[str, Any]:
        """
        Get the current execution context.
        
        Returns:
            Dictionary containing execution context
        """
        return {
            'lifetime_id': self.id,
            'tenant_id': self.tenant_id,
            'graph_id': self.graph.id,
            'status': self.status.value,
            'completed_nodes': list(self.completed_node_ids),
            'failed_nodes': list(self.failed_node_ids),
            'current_nodes': list(self.current_node_ids),
            'history': self.execution_history
        }
    
    def _check_completion(self) -> None:
        """
        Check if the lifetime execution is complete.
        """
        if self.status in [LifetimeStatus.COMPLETED, LifetimeStatus.FAILED, LifetimeStatus.ABORTED]:
            return
        
        # Check if all nodes are completed
        all_nodes = set(self.graph.nodes.keys())
        if self.completed_node_ids == all_nodes:
            self.status = LifetimeStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            self.current_node_ids.clear()
        
        # Check if any critical nodes failed
        elif self.failed_node_ids:
            self.status = LifetimeStatus.FAILED
            self.completed_at = datetime.utcnow()
            self.current_node_ids.clear()
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get the current execution progress.
        
        Returns:
            Dictionary with progress information
        """
        total_nodes = len(self.graph.nodes)
        completed_count = len(self.completed_node_ids)
        failed_count = len(self.failed_node_ids)
        running_count = len(self.current_node_ids)
        
        return {
            'total_nodes': total_nodes,
            'completed_nodes': completed_count,
            'failed_nodes': failed_count,
            'running_nodes': running_count,
            'progress_percentage': (completed_count / total_nodes) * 100 if total_nodes > 0 else 0,
            'status': self.status.value,
            'current_nodes': list(self.current_node_ids),
            'completed_node_ids': list(self.completed_node_ids),
            'failed_node_ids': list(self.failed_node_ids)
        }
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the lifetime to a dictionary.
        
        Returns:
            Dictionary representation of the lifetime
        """
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'graph_id': self.graph.id,
            'status': self.status.value,
            'metadata': self.metadata,
            'current_node_ids': list(self.current_node_ids),
            'completed_node_ids': list(self.completed_node_ids),
            'failed_node_ids': list(self.failed_node_ids),
            'execution_history': self.execution_history,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self) -> str:
        """String representation of the lifetime."""
        return f"AgentLifetime(id={self.id}, status={self.status.value}, progress={self.get_progress()['progress_percentage']:.1f}%)" 