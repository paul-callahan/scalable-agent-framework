export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: Record<string, any>;
}

export interface ErrorResponse {
  error: string;
  message: string;
  status: number;
  timestamp: string;
  path?: string;
  details?: Record<string, any>;
}

export class NetworkError extends Error {
  public originalError?: Error;
  
  constructor(message: string, originalError?: Error) {
    super(message);
    this.name = 'NetworkError';
    this.originalError = originalError;
  }
}

export class ValidationError extends Error {
  public errors: string[];
  
  constructor(message: string, errors: string[] = []) {
    super(message);
    this.name = 'ValidationError';
    this.errors = errors;
  }
}

export class TenantAccessError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TenantAccessError';
  }
}

export class FileProcessingError extends Error {
  public fileName?: string;
  
  constructor(message: string, fileName?: string) {
    super(message);
    this.name = 'FileProcessingError';
    this.fileName = fileName;
  }
}