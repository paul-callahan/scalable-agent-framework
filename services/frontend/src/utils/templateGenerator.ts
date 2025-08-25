import type { ExecutorFile } from '../types';

export const generatePlanTemplate = (planName: string): ExecutorFile => {
  const content = `from agentic_common.pb import PlanInput, PlanResult

def plan(plan_input: PlanInput) -> PlanResult:
    """
    Plan implementation for ${planName}
    
    Args:
        plan_input: Input data for the plan
        
    Returns:
        PlanResult: Result of the plan execution
    """
    # TODO: Implement plan logic here
    pass
`;

  return {
    name: 'plan.py',
    contents: content,
    creationDate: new Date().toISOString(),
    version: '1.0.0',
    updateDate: new Date().toISOString()
  };
};

export const generateTaskTemplate = (taskName: string): ExecutorFile => {
  const content = `from agentic_common.pb import TaskInput, TaskResult

def task(task_input: TaskInput) -> TaskResult:
    """
    Task implementation for ${taskName}
    
    Args:
        task_input: Input data for the task
        
    Returns:
        TaskResult: Result of the task execution
    """
    # TODO: Implement task logic here
    pass
`;

  return {
    name: 'task.py',
    contents: content,
    creationDate: new Date().toISOString(),
    version: '1.0.0',
    updateDate: new Date().toISOString()
  };
};

export const generateRequirementsTemplate = (): ExecutorFile => {
  const content = `# Add your Python dependencies here
# Example:
# requests>=2.25.1
# numpy>=1.21.0
`;

  return {
    name: 'requirements.txt',
    contents: content,
    creationDate: new Date().toISOString(),
    version: '1.0.0',
    updateDate: new Date().toISOString()
  };
};

export const createDefaultFilesForPlan = (planName: string): ExecutorFile[] => {
  return [
    generatePlanTemplate(planName),
    generateRequirementsTemplate()
  ];
};

export const createDefaultFilesForTask = (taskName: string): ExecutorFile[] => {
  return [
    generateTaskTemplate(taskName),
    generateRequirementsTemplate()
  ];
};