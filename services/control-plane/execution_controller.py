from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum


class ControlAction(Enum):
    """Control plane actions"""
    REJECT_EXECUTION = "REJECT_EXECUTION"
    PAUSE_LIFETIME = "PAUSE_LIFETIME"
    ABORT_LIFETIME = "ABORT_LIFETIME"


@dataclass
class ExecutionController:
    """Issues REJECT_EXECUTION, PAUSE_LIFETIME, or ABORT_LIFETIME events"""
    
    def __init__(self):
        """Initialize the execution controller"""
        pass
    
    def reject_execution(self, tenant_id: str, execution_id: str, reason: str) -> Dict[str, Any]:
        """Reject a specific execution"""
        return {
            "action": ControlAction.REJECT_EXECUTION,
            "tenant_id": tenant_id,
            "execution_id": execution_id,
            "reason": reason,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
    
    def pause_lifetime(self, tenant_id: str, lifetime_id: str, reason: str) -> Dict[str, Any]:
        """Pause an agent lifetime"""
        return {
            "action": ControlAction.PAUSE_LIFETIME,
            "tenant_id": tenant_id,
            "lifetime_id": lifetime_id,
            "reason": reason,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
    
    def abort_lifetime(self, tenant_id: str, lifetime_id: str, reason: str) -> Dict[str, Any]:
        """Abort an agent lifetime"""
        return {
            "action": ControlAction.ABORT_LIFETIME,
            "tenant_id": tenant_id,
            "lifetime_id": lifetime_id,
            "reason": reason,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        } 