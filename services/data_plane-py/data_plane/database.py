"""
Database connection management for data plane microservice.

This module provides database connection management using SQLAlchemy 2.0.31
async engine with connection pooling configuration, database URL construction
from environment variables, session factory, and health check queries.
"""

import os
from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from structlog import get_logger

from .models import Base

logger = get_logger(__name__)


class DatabaseManager:
    """
    Database connection manager for the data plane service.
    
    Handles connection pooling, session management, and health checks.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database manager.
        
        Args:
            database_url: Database URL (defaults to DATABASE_URL env var)
        """
        if database_url is None:
            database_url = self._get_database_url()
        
        self.database_url = database_url
        self.async_engine = None
        self.async_session_factory = None
        self.sync_engine = None
        self.sync_session_factory = None
        
    def _get_database_url(self) -> str:
        """
        Get database URL from environment variables.
        
        Returns:
            Database URL string
        """
        # Get individual components
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        database = os.getenv("DB_NAME", "agentic")
        username = os.getenv("DB_USER", "agentic")
        password = os.getenv("DB_PASSWORD", "agentic")
        
        # Construct URL
        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    
    async def initialize(self) -> None:
        """Initialize database connections and session factories."""
        try:
            # Create async engine
            self.async_engine = create_async_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_timeout=30,
            )
            
            # Create async session factory
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            # Create sync engine for migrations and health checks
            sync_url = self.database_url.replace("+asyncpg", "+psycopg2")
            self.sync_engine = create_engine(
                sync_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_timeout=30,
            )
            
            # Create sync session factory
            self.sync_session_factory = sessionmaker(
                self.sync_engine,
                expire_on_commit=False,
            )
            
            logger.info("Database connections initialized", 
                       url=self.database_url.replace(password, "***"))
            
        except Exception as e:
            logger.error("Failed to initialize database connections", error=str(e))
            raise
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.
        
        Yields:
            AsyncSession instance
        """
        if not self.async_session_factory:
            raise RuntimeError("Database not initialized")
        
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error("Database session error", error=str(e))
                raise
            finally:
                await session.close()
    
    def get_sync_session(self):
        """
        Get a sync database session.
        
        Returns:
            Session instance
        """
        if not self.sync_session_factory:
            raise RuntimeError("Database not initialized")
        
        return self.sync_session_factory()
    
    async def health_check(self) -> bool:
        """
        Perform database health check.
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            async with self.async_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()
            return True
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    async def close(self) -> None:
        """Close all database connections."""
        try:
            if self.async_engine:
                await self.async_engine.dispose()
            
            if self.sync_engine:
                self.sync_engine.dispose()
            
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error("Error closing database connections", error=str(e))
    
    def get_connection_info(self) -> dict:
        """
        Get database connection information.
        
        Returns:
            Dictionary with connection info
        """
        return {
            "url": self.database_url.replace(
                self.database_url.split("@")[0].split(":")[-1], 
                "***"
            ),
            "pool_size": self.async_engine.pool.size() if self.async_engine else None,
            "checked_in": self.async_engine.pool.checkedin() if self.async_engine else None,
            "checked_out": self.async_engine.pool.checkedout() if self.async_engine else None,
        }


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        DatabaseManager instance
    """
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
        await db_manager.initialize()
    return db_manager


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.
    
    Yields:
        AsyncSession instance
    """
    db_mgr = await get_database_manager()
    async for session in db_mgr.get_async_session():
        yield session 