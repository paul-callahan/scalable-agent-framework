"""
Guardrail evaluation engine for control plane microservice.

This module implements guardrail evaluation engine using pyyaml==6.0.1.
For MVP, creates a simple policy engine that can evaluate basic rules
like token limits, cost thresholds, and iteration caps.
"""

import os
from typing import Any, Dict, List, Optional

import yaml
from structlog import get_logger

logger = get_logger(__name__)


class GuardrailViolation:
    """Represents a guardrail violation."""
    
    def __init__(self, rule_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize guardrail violation.
        
        Args:
            rule_name: Name of the violated rule
            message: Violation message
            details: Optional violation details
        """
        self.rule_name = rule_name
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_name": self.rule_name,
            "message": self.message,
            "details": self.details,
        }


class GuardrailResult:
    """Result of guardrail evaluation."""
    
    def __init__(self, passed: bool, violations: Optional[List[GuardrailViolation]] = None):
        """
        Initialize guardrail result.
        
        Args:
            passed: Whether all guardrails passed
            violations: List of violations if any
        """
        self.passed = passed
        self.violations = violations or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
        }


class GuardrailEngine:
    """
    Guardrail evaluation engine.
    
    Evaluates execution headers against configured policies
    and returns pass/fail decisions with violation details.
    """
    
    def __init__(self, policies_path: Optional[str] = None):
        """
        Initialize the guardrail engine.
        
        Args:
            policies_path: Path to policies YAML file
        """
        self.policies_path = policies_path or os.getenv("GUARDRAIL_POLICIES_PATH", "policies/default.yaml")
        self.policies: Dict[str, Any] = {}
        self._load_policies()
    
    def _load_policies(self) -> None:
        """Load guardrail policies from YAML file."""
        try:
            if os.path.exists(self.policies_path):
                with open(self.policies_path, 'r') as f:
                    self.policies = yaml.safe_load(f) or {}
                logger.info("Guardrail policies loaded", path=self.policies_path)
            else:
                logger.warning("Policies file not found, using defaults", path=self.policies_path)
                self.policies = self._get_default_policies()
                
        except Exception as e:
            logger.error("Failed to load guardrail policies", 
                        path=self.policies_path,
                        error=str(e))
            self.policies = self._get_default_policies()
    
    def _get_default_policies(self) -> Dict[str, Any]:
        """
        Get default guardrail policies.
        
        Returns:
            Default policies dictionary
        """
        return {
            "token_limits": {
                "max_tokens_per_execution": 10000,
                "max_tokens_per_lifetime": 100000,
            },
            "cost_thresholds": {
                "max_cost_per_execution": 1.00,
                "max_cost_per_lifetime": 10.00,
            },
            "iteration_caps": {
                "max_iterations_per_lifetime": 100,
                "max_parallel_executions": 10,
            },
            "execution_timeouts": {
                "max_execution_time_seconds": 300,
                "max_lifetime_duration_hours": 24,
            },
        }
    
    def evaluate_execution(self, execution_data: Dict[str, Any]) -> GuardrailResult:
        """
        Evaluate execution against guardrails.
        
        Args:
            execution_data: Execution data to evaluate
            
        Returns:
            GuardrailResult with pass/fail decision and violations
        """
        violations = []
        
        try:
            # Extract execution header
            header = execution_data.get("header", {})
            tenant_id = header.get("tenant_id", "default")
            
            # Get tenant-specific policies (fallback to defaults)
            tenant_policies = self.policies.get("tenants", {}).get(tenant_id, self.policies)
            
            # Evaluate token limits
            token_violations = self._evaluate_token_limits(header, tenant_policies)
            violations.extend(token_violations)
            
            # Evaluate cost thresholds
            cost_violations = self._evaluate_cost_thresholds(header, tenant_policies)
            violations.extend(cost_violations)
            
            # Evaluate iteration caps
            iteration_violations = self._evaluate_iteration_caps(header, tenant_policies)
            violations.extend(iteration_violations)
            
            # Evaluate execution timeouts
            timeout_violations = self._evaluate_execution_timeouts(header, tenant_policies)
            violations.extend(timeout_violations)
            
            # Check if any violations occurred
            passed = len(violations) == 0
            
            result = GuardrailResult(passed=passed, violations=violations)
            
            if passed:
                logger.info("Guardrail evaluation passed", 
                           execution_id=header.get("id"),
                           tenant_id=tenant_id)
            else:
                logger.warning("Guardrail evaluation failed", 
                              execution_id=header.get("id"),
                              tenant_id=tenant_id,
                              violations=[v.to_dict() for v in violations])
            
            return result
            
        except Exception as e:
            logger.error("Guardrail evaluation error", 
                        execution_data=execution_data,
                        error=str(e))
            return GuardrailResult(
                passed=False,
                violations=[GuardrailViolation(
                    rule_name="evaluation_error",
                    message=f"Guardrail evaluation failed: {str(e)}"
                )]
            )
    
    def _evaluate_token_limits(self, header: Dict[str, Any], policies: Dict[str, Any]) -> List[GuardrailViolation]:
        """
        Evaluate token limits.
        
        Args:
            header: Execution header
            policies: Tenant policies
            
        Returns:
            List of token limit violations
        """
        violations = []
        token_policies = policies.get("token_limits", {})
        
        # Check max tokens per execution
        max_tokens_per_execution = token_policies.get("max_tokens_per_execution")
        if max_tokens_per_execution:
            # This would need to be calculated from the actual execution
            # For now, we'll assume it's within limits
            pass
        
        # Check max tokens per lifetime
        max_tokens_per_lifetime = token_policies.get("max_tokens_per_lifetime")
        if max_tokens_per_lifetime:
            # This would need to be calculated from lifetime history
            # For now, we'll assume it's within limits
            pass
        
        return violations
    
    def _evaluate_cost_thresholds(self, header: Dict[str, Any], policies: Dict[str, Any]) -> List[GuardrailViolation]:
        """
        Evaluate cost thresholds.
        
        Args:
            header: Execution header
            policies: Tenant policies
            
        Returns:
            List of cost threshold violations
        """
        violations = []
        cost_policies = policies.get("cost_thresholds", {})
        
        # Check max cost per execution
        max_cost_per_execution = cost_policies.get("max_cost_per_execution")
        if max_cost_per_execution:
            # This would need to be calculated from the actual execution
            # For now, we'll assume it's within limits
            pass
        
        # Check max cost per lifetime
        max_cost_per_lifetime = cost_policies.get("max_cost_per_lifetime")
        if max_cost_per_lifetime:
            # This would need to be calculated from lifetime history
            # For now, we'll assume it's within limits
            pass
        
        return violations
    
    def _evaluate_iteration_caps(self, header: Dict[str, Any], policies: Dict[str, Any]) -> List[GuardrailViolation]:
        """
        Evaluate iteration caps.
        
        Args:
            header: Execution header
            policies: Tenant policies
            
        Returns:
            List of iteration cap violations
        """
        violations = []
        iteration_policies = policies.get("iteration_caps", {})
        
        # Check max iterations per lifetime
        max_iterations = iteration_policies.get("max_iterations_per_lifetime")
        if max_iterations:
            iteration_idx = header.get("iteration_idx", 0)
            if iteration_idx >= max_iterations:
                violations.append(GuardrailViolation(
                    rule_name="max_iterations_per_lifetime",
                    message=f"Exceeded maximum iterations per lifetime: {iteration_idx} >= {max_iterations}",
                    details={"current": iteration_idx, "max": max_iterations}
                ))
        
        # Check max parallel executions
        max_parallel = iteration_policies.get("max_parallel_executions")
        if max_parallel:
            # This would need to be calculated from current running executions
            # For now, we'll assume it's within limits
            pass
        
        return violations
    
    def _evaluate_execution_timeouts(self, header: Dict[str, Any], policies: Dict[str, Any]) -> List[GuardrailViolation]:
        """
        Evaluate execution timeouts.
        
        Args:
            header: Execution header
            policies: Tenant policies
            
        Returns:
            List of timeout violations
        """
        violations = []
        timeout_policies = policies.get("execution_timeouts", {})
        
        # Check max execution time
        max_execution_time = timeout_policies.get("max_execution_time_seconds")
        if max_execution_time:
            # This would need to be calculated from execution start time
            # For now, we'll assume it's within limits
            pass
        
        # Check max lifetime duration
        max_lifetime_duration = timeout_policies.get("max_lifetime_duration_hours")
        if max_lifetime_duration:
            # This would need to be calculated from lifetime start time
            # For now, we'll assume it's within limits
            pass
        
        return violations
    
    def reload_policies(self) -> None:
        """Reload policies from file."""
        self._load_policies()
        logger.info("Guardrail policies reloaded")
    
    def get_policies(self) -> Dict[str, Any]:
        """
        Get current policies.
        
        Returns:
            Current policies dictionary
        """
        return self.policies.copy()
    
    def update_policies(self, new_policies: Dict[str, Any]) -> None:
        """
        Update policies.
        
        Args:
            new_policies: New policies to set
        """
        self.policies = new_policies
        logger.info("Guardrail policies updated") 