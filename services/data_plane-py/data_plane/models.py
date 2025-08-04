"""
SQLAlchemy models for data plane microservice.

This module defines the database models for TaskExecution and PlanExecution
tables using SQLAlchemy 2.0.31 with all fields from the protobuf ExecutionHeader
plus result data.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Float,
    Index,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class TaskExecution(Base):
    """
    TaskExecution database model.
    
    Stores TaskExecution messages with all protobuf fields plus
    additional database-specific fields.
    """
    
    __tablename__ = "task_executions"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # ExecutionHeader fields
    parent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False)
    lifetime_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    attempt: Mapped[int] = mapped_column(BigInteger, nullable=False)
    iteration_idx: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[str] = mapped_column(String(255), nullable=False)  # ISO-8601 timestamp
    status: Mapped[str] = mapped_column(
        Enum("PENDING", "RUNNING", "SUCCEEDED", "FAILED", name="execution_status"),
        nullable=False
    )
    edge_taken: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Task-specific fields
    task_type: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Result data (stored as JSONB for flexibility)
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    result_mime_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    result_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Database-specific fields
    db_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    db_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_task_executions_tenant_id", "tenant_id"),
        Index("idx_task_executions_execution_id", "tenant_id", "id"),
        Index("idx_task_executions_created_at", "tenant_id", "created_at"),
        Index("idx_task_executions_status", "tenant_id", "status"),
        Index("idx_task_executions_lifetime_id", "tenant_id", "lifetime_id"),
        Index("idx_task_executions_graph_id", "tenant_id", "graph_id"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "graph_id": self.graph_id,
            "lifetime_id": self.lifetime_id,
            "tenant_id": self.tenant_id,
            "attempt": self.attempt,
            "iteration_idx": self.iteration_idx,
            "created_at": self.created_at,
            "status": self.status,
            "edge_taken": self.edge_taken,
            "task_type": self.task_type,
            "result_data": self.result_data,
            "result_mime_type": self.result_mime_type,
            "result_size_bytes": self.result_size_bytes,
            "error_message": self.error_message,
            "db_created_at": self.db_created_at.isoformat() if self.db_created_at else None,
            "db_updated_at": self.db_updated_at.isoformat() if self.db_updated_at else None,
        }


class PlanExecution(Base):
    """
    PlanExecution database model.
    
    Stores PlanExecution messages with all protobuf fields plus
    additional database-specific fields.
    """
    
    __tablename__ = "plan_executions"
    
    # Primary key
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    
    # ExecutionHeader fields
    parent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    graph_id: Mapped[str] = mapped_column(String(255), nullable=False)
    lifetime_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False)
    attempt: Mapped[int] = mapped_column(BigInteger, nullable=False)
    iteration_idx: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[str] = mapped_column(String(255), nullable=False)  # ISO-8601 timestamp
    status: Mapped[str] = mapped_column(
        Enum("PENDING", "RUNNING", "SUCCEEDED", "FAILED", name="execution_status"),
        nullable=False
    )
    edge_taken: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Plan-specific fields
    plan_type: Mapped[str] = mapped_column(String(255), nullable=False)
    input_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Result data (stored as JSONB for flexibility)
    result_next_task_ids: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    result_metadata: Mapped[Optional[Dict[str, str]]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Database-specific fields
    db_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    db_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_plan_executions_tenant_id", "tenant_id"),
        Index("idx_plan_executions_execution_id", "tenant_id", "id"),
        Index("idx_plan_executions_created_at", "tenant_id", "created_at"),
        Index("idx_plan_executions_status", "tenant_id", "status"),
        Index("idx_plan_executions_lifetime_id", "tenant_id", "lifetime_id"),
        Index("idx_plan_executions_graph_id", "tenant_id", "graph_id"),
        Index("idx_plan_executions_input_task_id", "tenant_id", "input_task_id"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "graph_id": self.graph_id,
            "lifetime_id": self.lifetime_id,
            "tenant_id": self.tenant_id,
            "attempt": self.attempt,
            "iteration_idx": self.iteration_idx,
            "created_at": self.created_at,
            "status": self.status,
            "edge_taken": self.edge_taken,
            "plan_type": self.plan_type,
            "input_task_id": self.input_task_id,
            "result_next_task_ids": self.result_next_task_ids,
            "result_metadata": self.result_metadata,
            "error_message": self.error_message,
            "confidence": self.confidence,
            "db_created_at": self.db_created_at.isoformat() if self.db_created_at else None,
            "db_updated_at": self.db_updated_at.isoformat() if self.db_updated_at else None,
        } 