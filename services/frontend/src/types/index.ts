export interface ExecutorFile {
  name: string;
  contents: string;
  creationDate: string;
  version: string;
  updateDate: string;
}

export interface PlanDto {
  name: string;
  label: string;
  upstreamTaskIds: string[];
  files: ExecutorFile[];
}

export interface TaskDto {
  name: string;
  label: string;
  upstreamPlanId: string;
  files: ExecutorFile[];
}

export type GraphStatus = 'NEW' | 'RUNNING' | 'STOPPED' | 'ERROR';

export interface AgentGraphDto {
  id: string;
  name: string;
  tenantId: string;
  status: GraphStatus;
  plans: PlanDto[];
  tasks: TaskDto[];
  planToTasks: Record<string, string[]>;
  taskToPlan: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

export interface AgentGraphSummary {
  id: string;
  name: string;
  status: GraphStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CreateGraphRequest {
  name: string;
  tenantId: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface NodeNameValidationRequest {
  nodeName: string;
  graphId: string;
  excludeNodeId?: string;
  existingNodeNames?: string[];
}

export interface ExecutionResponse {
  success: boolean;
  message: string;
}

export interface GraphStatusUpdate {
  status: GraphStatus;
}

// Re-export error types for convenience
export type {
  ApiError,
  ErrorResponse,
  NetworkError,
  ValidationError,
  TenantAccessError,
  FileProcessingError,
} from './errors';