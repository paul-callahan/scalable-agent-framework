#!/usr/bin/env python3
"""
Script to generate Python files for test graphs.
"""

import os
import pathlib

def create_plan_files(base_path, plan_name):
    """Create plan.py and requirements.txt for a plan."""
    plan_dir = base_path / "plans" / plan_name
    plan_dir.mkdir(parents=True, exist_ok=True)
    
    # Create plan.py
    plan_py = plan_dir / "plan.py"
    plan_py.write_text(f'''def plan(upstream_results):
    """{plan_name.replace('_', ' ').title()} implementation."""
    return {{"data": "{plan_name}_result"}}
''')
    
    # Create requirements.txt
    requirements = plan_dir / "requirements.txt"
    requirements.write_text("requests>=2.25.0\n")

def create_task_files(base_path, task_name):
    """Create task.py and requirements.txt for a task."""
    task_dir = base_path / "tasks" / task_name
    task_dir.mkdir(parents=True, exist_ok=True)
    
    # Create task.py
    task_py = task_dir / "task.py"
    task_py.write_text(f'''def execute(upstream_plan):
    """{task_name.replace('_', ' ').title()} implementation."""
    return {{"data": "{task_name}_result"}}
''')
    
    # Create requirements.txt
    requirements = task_dir / "requirements.txt"
    requirements.write_text("pandas>=1.3.0\n")

def main():
    """Generate all test files."""
    base_path = pathlib.Path(__file__).parent
    
    # Simple graph files (from the original valid_graph)
    simple_graph_path = base_path / "valid_graphs" / "simple_graph"
    plans = ["plan_data_collection", "plan_analysis"]
    tasks = ["task_fetch_data", "task_process_data", "task_generate_report"]
    
    for plan in plans:
        create_plan_files(simple_graph_path, plan)
    
    for task in tasks:
        create_task_files(simple_graph_path, task)
    
    # Cycle graph files
    cycle_graph_path = base_path / "valid_graphs" / "cycle_graph"
    plans = ["plan1", "plan2"]  # Use actual node names from DOT file
    tasks = ["task1", "task2"]
    
    for plan in plans:
        create_plan_files(cycle_graph_path, plan)
    
    for task in tasks:
        create_task_files(cycle_graph_path, task)
    
    # Multi-plan graph files
    multi_plan_path = base_path / "valid_graphs" / "multi_plan_graph"
    plans = ["plan_data_ingestion", "plan_data_processing", "plan_analysis", "plan_reporting"]
    tasks = ["task_fetch_data", "task_validate_data", "task_transform_data", "task_analyze_data", "task_generate_report", "task_send_notification"]
    
    for plan in plans:
        create_plan_files(multi_plan_path, plan)
    
    for task in tasks:
        create_task_files(multi_plan_path, task)
    
    # Parallel tasks graph files
    parallel_path = base_path / "valid_graphs" / "parallel_tasks_graph"
    plans = ["plan_data_collection", "plan_parallel_processing", "plan_aggregation"]
    tasks = ["task_fetch_user_data", "task_fetch_product_data", "task_process_user_data", "task_process_product_data", "task_aggregate_results"]
    
    for plan in plans:
        create_plan_files(parallel_path, plan)
    
    for task in tasks:
        create_task_files(parallel_path, task)
    
    print("Generated all test files successfully!")

if __name__ == "__main__":
    main() 