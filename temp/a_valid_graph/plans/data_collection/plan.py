"""
Test plan for data collection.

This is a test plan that demonstrates the expected structure for plan implementations.
"""
from typing import List

# Mock imports - in a real implementation these would be actual types
class TaskResult:
    def __init__(self, data):
        self.data = data

class PlanResult:
    def __init__(self, data):
        self.data = data

def plan(upstream_results: List[TaskResult]) -> PlanResult:
    """
    Plan function that processes upstream task results.
    
    Args:
        upstream_results: List of results from upstream tasks
        
    Returns:
        PlanResult: The plan result
    """
    # Simple implementation that combines upstream results
    combined_data = []
    for result in upstream_results:
        combined_data.extend(result.data)
    
    return PlanResult(combined_data) 