"""
AgentLifetime class for the agentic framework.

AgentLifetime represents one runtime instance of an AgentGraph executing to completion.
It manages the execution state and provides control operations like pause/resume/abort.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from .graph import AgentGraph
from .task import Task, TaskResult
from .plan import Plan, PlanResult


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
        
        # Store node results for passing between executions
        self.node_results: Dict[str, Union[TaskResult, PlanResult]] = {}
        
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
    
    def complete_node(self, node_id: str, result: Union[TaskResult, PlanResult]) -> None:
        """
        Mark a node as completed with its result.
        
        Args:
            node_id: ID of the completed node
            result: Result from the node execution (TaskResult or PlanResult)
        """
        if node_id not in self.current_node_ids:
            raise ValueError(f"Node {node_id} is not currently running")
        
        self.current_node_ids.remove(node_id)
        self.completed_node_ids.add(node_id)
        
        # Store the result for use by subsequent nodes
        self._store_node_result(node_id, result)
        
        # Record completion in history
        self.execution_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'complete_node',
            'node_id': node_id,
            'result_type': type(result).__name__,
            'has_error': getattr(result, 'error_message', None) is not None
        })
        
        # If this is a Plan node, add the next tasks to current_node_ids
        if isinstance(result, PlanResult) and not result.error_message:
            for task_id in result.next_task_ids:
                if task_id in self.graph.nodes:
                    self.current_node_ids.add(task_id)
        
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
    
    async def execute_node(self, node_id: str) -> Union[TaskResult, PlanResult]:
        """
        Execute a specific node (Task or Plan).
        
        Args:
            node_id: ID of the node to execute
            
        Returns:
            TaskResult or PlanResult from the execution
            
        Raises:
            ValueError: If node doesn't exist or is wrong type
            RuntimeError: If execution fails
        """
        node = self.graph.get_node(node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found in graph")
        
        try:
            if isinstance(node, Task):
                # Task needs PlanResult from previous step
                last_plan_result = self._get_last_plan_result()
                result = await node.execute(last_plan_result)
                if not isinstance(result, TaskResult):
                    raise RuntimeError(f"Task {node_id} returned {type(result)}, expected TaskResult")
                return result
                
            elif isinstance(node, Plan):
                # Plan needs TaskResult from previous step
                last_task_result = self._get_last_task_result()
                result = await node.plan(last_task_result)
                if not isinstance(result, PlanResult):
                    raise RuntimeError(f"Plan {node_id} returned {type(result)}, expected PlanResult")
                return result
                
            else:
                raise ValueError(f"Node {node_id} is neither Task nor Plan: {type(node)}")
                
        except Exception as e:
            # Create error result based on node type
            if isinstance(node, Task):
                return TaskResult(error_message=str(e))
            else:
                return PlanResult(next_task_ids=[], error_message=str(e))

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
    
    def _store_node_result(self, node_id: str, result: Union[TaskResult, PlanResult]) -> None:
        """
        Store the result of a node execution.
        
        Args:
            node_id: ID of the node
            result: Result from the node execution
        """
        self.node_results[node_id] = result

    def _get_last_plan_result(self) -> PlanResult:
        """
        Get the most recent PlanResult for Task execution.
        
        Returns:
            Most recent PlanResult, or empty PlanResult if none exists
        """
        # Find the most recent Plan execution
        for entry in reversed(self.execution_history):
            if entry.get('action') == 'complete_node':
                node_id = entry.get('node_id')
                if node_id in self.node_results:
                    result = self.node_results[node_id]
                    if isinstance(result, PlanResult):
                        return result
        
        # Return empty PlanResult if no previous plan found
        return PlanResult(next_task_ids=[])

    def _get_last_task_result(self) -> TaskResult:
        """
        Get the most recent TaskResult for Plan execution.
        
        Returns:
            Most recent TaskResult, or empty TaskResult if none exists
        """
        # Find the most recent Task execution
        for entry in reversed(self.execution_history):
            if entry.get('action') == 'complete_node':
                node_id = entry.get('node_id')
                if node_id in self.node_results:
                    result = self.node_results[node_id]
                    if isinstance(result, TaskResult):
                        return result
        
        # Return empty TaskResult if no previous task found
        return TaskResult()

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
            'history': self.execution_history,
            'node_results': {k: type(v).__name__ for k, v in self.node_results.items()}
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
        # Serialize node results (simplified for JSON compatibility)
        serialized_results = {}
        for node_id, result in self.node_results.items():
            if isinstance(result, TaskResult):
                serialized_results[node_id] = {
                    'type': 'TaskResult',
                    'mime_type': result.mime_type,
                    'size_bytes': result.size_bytes,
                    'has_error': result.error_message is not None,
                    'error_message': result.error_message
                }
            elif isinstance(result, PlanResult):
                serialized_results[node_id] = {
                    'type': 'PlanResult',
                    'next_task_ids': result.next_task_ids,
                    'confidence': result.confidence,
                    'has_error': result.error_message is not None,
                    'error_message': result.error_message
                }
        
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
            'node_results': serialized_results,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self) -> str:
        """String representation of the lifetime."""
        return f"AgentLifetime(id={self.id}, status={self.status.value}, progress={self.get_progress()['progress_percentage']:.1f}%)" 
