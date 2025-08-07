"""
Sample plan implementation for testing.
"""

from agentic_common.pb import PlanInput, PlanResult


def plan(plan_input):
    """
    Sample plan implementation for testing.
    
    Args:
        plan_input: PlanInput protobuf message
        
    Returns:
        PlanResult with next task names
    """
    # Basic validation
    if not plan_input.plan_name:
        return PlanResult(
            next_task_names=[],
            upstream_tasks_results=[],
            error_message="Plan name is required"
        )
    
    # Extract upstream task results
    upstream_results = []
    for task_exec in plan_input.task_executions:
        if task_exec.result:
            upstream_results.append(task_exec.result)
    
    # Simple plan logic: return next task names based on plan parameters
    next_task_names = []
    if plan_input.plan_parameters.get("include_sample_task", False):
        next_task_names.append("sample-task")
    
    if plan_input.plan_parameters.get("include_validation_task", False):
        next_task_names.append("validation-task")
    
    # Default next task if no specific tasks are requested
    if not next_task_names:
        next_task_names.append("default-task")
    
    return PlanResult(
        next_task_names=next_task_names,
        upstream_tasks_results=upstream_results,
        error_message=""
    ) 