"""
Test task for data fetching.

This is a test task that demonstrates the expected structure for task implementations.
"""

# Mock imports - in a real implementation these would be actual types
class PlanResult:
    def __init__(self, data):
        self.data = data

class TaskResult:
    def __init__(self, data):
        self.data = data

def execute(upstream_plan: PlanResult) -> TaskResult:
    """
    Task function that processes upstream plan results.
    
    Args:
        upstream_plan: Result from the upstream plan
        
    Returns:
        TaskResult: The task result
    """
    # Simple implementation that processes the plan data
    processed_data = [item * 2 for item in upstream_plan.data]
    
    return TaskResult(processed_data) 