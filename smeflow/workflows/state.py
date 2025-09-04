"""
Workflow State Management for LangGraph workflows.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class WorkflowState(BaseModel):
    """
    Represents the state of a workflow execution.
    
    This state is passed between workflow nodes and persisted
    for recovery and monitoring purposes.
    """
    
    # Execution metadata
    workflow_id: uuid.UUID
    execution_id: Optional[uuid.UUID] = None
    tenant_id: str
    current_node: Optional[str] = None
    status: str = "running"  # running, completed, failed, paused
    
    # Data payload
    data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Error handling
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # African market context
    region: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"
    language: str = "en"
    
    # Agent integration
    agent_id: Optional[uuid.UUID] = None
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Cost tracking
    total_cost_usd: float = 0.0
    tokens_used: int = 0
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
    
    def add_error(self, error: str, node: Optional[str] = None) -> None:
        """Add an error to the workflow state."""
        self.errors.append({
            "error": error,
            "node": node or self.current_node,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_count": self.retry_count
        })
        self.updated_at = datetime.utcnow()
    
    def set_current_node(self, node: str) -> None:
        """Set the current node being executed."""
        self.current_node = node
        self.updated_at = datetime.utcnow()
    
    def complete(self) -> None:
        """Mark the workflow as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def fail(self, error: str) -> None:
        """Mark the workflow as failed."""
        self.status = "failed"
        self.add_error(error)
        self.completed_at = datetime.utcnow()
    
    def pause(self) -> None:
        """Pause the workflow execution."""
        self.status = "paused"
        self.updated_at = datetime.utcnow()
    
    def resume(self) -> None:
        """Resume the workflow execution."""
        self.status = "running"
        self.updated_at = datetime.utcnow()
    
    def should_retry(self) -> bool:
        """Check if the workflow should retry on failure."""
        return self.retry_count < self.max_retries
    
    def increment_retry(self) -> None:
        """Increment the retry counter."""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_cost(self, cost_usd: float, tokens: int = 0) -> None:
        """Add cost and token usage to the workflow."""
        self.total_cost_usd += cost_usd
        self.tokens_used += tokens
        self.updated_at = datetime.utcnow()
    
    def get_duration_ms(self) -> Optional[int]:
        """Get the workflow duration in milliseconds."""
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None
