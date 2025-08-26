import { describe, it, expect } from 'vitest';
import {
  generatePlanTemplate,
  generateTaskTemplate,
  generateRequirementsTemplate,
  createDefaultFilesForPlan,
  createDefaultFilesForTask
} from '../templateGenerator';

describe('templateGenerator', () => {
  describe('generatePlanTemplate', () => {
    it('should generate a plan template with correct imports and signature', () => {
      const planName = 'test-plan';
      const template = generatePlanTemplate(planName);

      expect(template.name).toBe('plan.py');
      expect(template.contents).toContain('from agentic_common.pb import PlanInput, PlanResult');
      expect(template.contents).toContain('def plan(plan_input: PlanInput) -> PlanResult:');
      expect(template.contents).toContain(`Plan implementation for ${planName}`);
      expect(template.version).toBe('1.0.0');
    });

    it('should have valid timestamps', () => {
      const template = generatePlanTemplate('test');
      const creationDate = new Date(template.creationDate);
      const updateDate = new Date(template.updateDate);

      expect(creationDate.getTime()).toBeLessThanOrEqual(Date.now());
      expect(updateDate.getTime()).toBeLessThanOrEqual(Date.now());
    });
  });

  describe('generateTaskTemplate', () => {
    it('should generate a task template with correct imports and signature', () => {
      const taskName = 'test-task';
      const template = generateTaskTemplate(taskName);

      expect(template.name).toBe('task.py');
      expect(template.contents).toContain('from agentic_common.pb import TaskInput, TaskResult');
      expect(template.contents).toContain('def task(task_input: TaskInput) -> TaskResult:');
      expect(template.contents).toContain(`Task implementation for ${taskName}`);
      expect(template.version).toBe('1.0.0');
    });
  });

  describe('generateRequirementsTemplate', () => {
    it('should generate a requirements.txt template', () => {
      const template = generateRequirementsTemplate();

      expect(template.name).toBe('requirements.txt');
      expect(template.contents).toContain('# Add your Python dependencies here');
      expect(template.contents).toContain('# requests>=2.25.1');
      expect(template.version).toBe('1.0.0');
    });
  });

  describe('createDefaultFilesForPlan', () => {
    it('should create plan.py and requirements.txt files', () => {
      const files = createDefaultFilesForPlan('test-plan');

      expect(files).toHaveLength(2);
      expect(files.find(f => f.name === 'plan.py')).toBeDefined();
      expect(files.find(f => f.name === 'requirements.txt')).toBeDefined();
    });
  });

  describe('createDefaultFilesForTask', () => {
    it('should create task.py and requirements.txt files', () => {
      const files = createDefaultFilesForTask('test-task');

      expect(files).toHaveLength(2);
      expect(files.find(f => f.name === 'task.py')).toBeDefined();
      expect(files.find(f => f.name === 'requirements.txt')).toBeDefined();
    });
  });
});