"""
Workflow health monitoring and failure detection system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .state import WorkflowState


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels for workflows."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    RECOVERING = "recovering"


class FailurePattern(Enum):
    """Types of failure patterns detected."""
    TRANSIENT = "transient"
    RESOURCE = "resource"
    PERSISTENT = "persistent"
    CASCADING = "cascading"


@dataclass
class HealthMetrics:
    """Health metrics for a workflow."""
    success_rate: float
    average_duration: float
    error_rate: float
    recovery_success_rate: float
    last_failure_time: Optional[datetime]
    consecutive_failures: int
    total_executions: int
    total_recoveries: int


@dataclass
class FailureEvent:
    """Represents a workflow failure event."""
    timestamp: datetime
    workflow_id: str
    execution_id: str
    error_message: str
    failure_pattern: FailurePattern
    recovery_attempted: bool
    recovery_successful: bool
    duration_ms: Optional[int]


class WorkflowHealthMonitor:
    """
    Monitors workflow health and detects failure patterns.
    
    Provides real-time health monitoring, failure detection,
    and automated alerts for workflow issues.
    """
    
    def __init__(self, tenant_id: str):
        """
        Initialize health monitor.
        
        Args:
            tenant_id: Tenant identifier for multi-tenant isolation
        """
        self.tenant_id = tenant_id
        self.health_metrics: Dict[str, HealthMetrics] = {}
        self.failure_events: List[FailureEvent] = []
        self.alert_thresholds = {
            "error_rate": 0.2,  # 20% error rate threshold
            "consecutive_failures": 5,
            "recovery_failure_rate": 0.5,  # 50% recovery failure rate
            "response_time_degradation": 2.0  # 2x normal response time
        }
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self, check_interval: int = 60):
        """
        Start continuous health monitoring.
        
        Args:
            check_interval: Health check interval in seconds
        """
        if self._monitoring_active:
            logger.warning("Health monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(check_interval)
        )
        logger.info(f"Started workflow health monitoring for tenant {self.tenant_id}")
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Stopped workflow health monitoring for tenant {self.tenant_id}")
    
    async def _monitoring_loop(self, check_interval: int):
        """
        Main monitoring loop.
        
        Args:
            check_interval: Check interval in seconds
        """
        while self._monitoring_active:
            try:
                await self._perform_health_check()
                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(check_interval)
    
    async def _perform_health_check(self):
        """Perform comprehensive health check on all workflows."""
        current_time = datetime.utcnow()
        
        for workflow_id, metrics in self.health_metrics.items():
            # Check for critical health issues
            health_status = self._assess_workflow_health(workflow_id, metrics)
            
            # Generate alerts if needed
            if health_status in [HealthStatus.CRITICAL, HealthStatus.DEGRADED]:
                await self._generate_health_alert(workflow_id, health_status, metrics)
            
            # Clean up old failure events (keep last 24 hours)
            cutoff_time = current_time - timedelta(hours=24)
            self.failure_events = [
                event for event in self.failure_events
                if event.timestamp > cutoff_time
            ]
    
    def record_execution(
        self,
        workflow_id: str,
        execution_id: str,
        success: bool,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        Record workflow execution for health tracking.
        
        Args:
            workflow_id: Workflow identifier
            execution_id: Execution identifier
            success: Whether execution was successful
            duration_ms: Execution duration in milliseconds
            error_message: Error message if execution failed
        """
        # Initialize metrics if not exists
        if workflow_id not in self.health_metrics:
            self.health_metrics[workflow_id] = HealthMetrics(
                success_rate=1.0,
                average_duration=0.0,
                error_rate=0.0,
                recovery_success_rate=1.0,
                last_failure_time=None,
                consecutive_failures=0,
                total_executions=0,
                total_recoveries=0
            )
        
        metrics = self.health_metrics[workflow_id]
        metrics.total_executions += 1
        
        # Update success/error rates
        if success:
            metrics.consecutive_failures = 0
            # Update success rate (exponential moving average)
            metrics.success_rate = 0.9 * metrics.success_rate + 0.1 * 1.0
            metrics.error_rate = 0.9 * metrics.error_rate + 0.1 * 0.0
        else:
            metrics.consecutive_failures += 1
            metrics.last_failure_time = datetime.utcnow()
            metrics.success_rate = 0.9 * metrics.success_rate + 0.1 * 0.0
            metrics.error_rate = 0.9 * metrics.error_rate + 0.1 * 1.0
            
            # Record failure event
            if error_message:
                failure_pattern = self._classify_failure_pattern(error_message)
                self.failure_events.append(FailureEvent(
                    timestamp=datetime.utcnow(),
                    workflow_id=workflow_id,
                    execution_id=execution_id,
                    error_message=error_message,
                    failure_pattern=failure_pattern,
                    recovery_attempted=False,
                    recovery_successful=False,
                    duration_ms=duration_ms
                ))
        
        # Update average duration
        if duration_ms is not None:
            if metrics.average_duration == 0:
                metrics.average_duration = float(duration_ms)
            else:
                # Exponential moving average
                metrics.average_duration = (
                    0.8 * metrics.average_duration + 0.2 * duration_ms
                )
    
    def record_recovery_attempt(
        self,
        workflow_id: str,
        execution_id: str,
        success: bool,
        recovery_strategy: str
    ):
        """
        Record recovery attempt for health tracking.
        
        Args:
            workflow_id: Workflow identifier
            execution_id: Execution identifier
            success: Whether recovery was successful
            recovery_strategy: Strategy used for recovery
        """
        if workflow_id not in self.health_metrics:
            return
        
        metrics = self.health_metrics[workflow_id]
        metrics.total_recoveries += 1
        
        # Update recovery success rate
        recovery_success = 1.0 if success else 0.0
        if metrics.recovery_success_rate == 1.0 and metrics.total_recoveries == 1:
            metrics.recovery_success_rate = recovery_success
        else:
            metrics.recovery_success_rate = (
                0.8 * metrics.recovery_success_rate + 0.2 * recovery_success
            )
        
        # Update failure event if exists
        for event in reversed(self.failure_events):
            if (event.workflow_id == workflow_id and 
                event.execution_id == execution_id and
                not event.recovery_attempted):
                event.recovery_attempted = True
                event.recovery_successful = success
                break
        
        logger.info(
            f"Recovery attempt for {workflow_id}: {recovery_strategy} - "
            f"{'Success' if success else 'Failed'}"
        )
    
    def _classify_failure_pattern(self, error_message: str) -> FailurePattern:
        """
        Classify failure pattern based on error message.
        
        Args:
            error_message: Error message to analyze
            
        Returns:
            Classified failure pattern
        """
        error_lower = error_message.lower()
        
        # Transient failures
        transient_keywords = [
            "timeout", "connection", "network", "temporary", "unavailable",
            "rate limit", "throttle", "busy", "retry"
        ]
        if any(keyword in error_lower for keyword in transient_keywords):
            return FailurePattern.TRANSIENT
        
        # Resource failures
        resource_keywords = [
            "memory", "disk", "cpu", "quota", "limit", "capacity",
            "resource", "storage", "space"
        ]
        if any(keyword in error_lower for keyword in resource_keywords):
            return FailurePattern.RESOURCE
        
        # Persistent failures (validation, configuration, etc.)
        persistent_keywords = [
            "validation", "invalid", "missing", "required", "format",
            "syntax", "configuration", "permission", "unauthorized"
        ]
        if any(keyword in error_lower for keyword in persistent_keywords):
            return FailurePattern.PERSISTENT
        
        # Default to transient for unknown patterns
        return FailurePattern.TRANSIENT
    
    def _assess_workflow_health(
        self, 
        workflow_id: str, 
        metrics: HealthMetrics
    ) -> HealthStatus:
        """
        Assess overall health status of a workflow.
        
        Args:
            workflow_id: Workflow identifier
            metrics: Current health metrics
            
        Returns:
            Overall health status
        """
        # Critical conditions
        if (metrics.consecutive_failures >= self.alert_thresholds["consecutive_failures"] or
            metrics.error_rate >= 0.8 or
            metrics.recovery_success_rate <= 0.2):
            return HealthStatus.CRITICAL
        
        # Degraded conditions
        if (metrics.error_rate >= self.alert_thresholds["error_rate"] or
            metrics.recovery_success_rate <= self.alert_thresholds["recovery_failure_rate"] or
            metrics.consecutive_failures >= 3):
            return HealthStatus.DEGRADED
        
        # Check if currently recovering
        recent_failures = [
            event for event in self.failure_events
            if (event.workflow_id == workflow_id and
                event.timestamp > datetime.utcnow() - timedelta(minutes=10))
        ]
        if any(event.recovery_attempted for event in recent_failures):
            return HealthStatus.RECOVERING
        
        return HealthStatus.HEALTHY
    
    async def _generate_health_alert(
        self,
        workflow_id: str,
        health_status: HealthStatus,
        metrics: HealthMetrics
    ):
        """
        Generate health alert for workflow issues.
        
        Args:
            workflow_id: Workflow identifier
            health_status: Current health status
            metrics: Health metrics
        """
        alert_data = {
            "tenant_id": self.tenant_id,
            "workflow_id": workflow_id,
            "health_status": health_status.value,
            "error_rate": metrics.error_rate,
            "consecutive_failures": metrics.consecutive_failures,
            "recovery_success_rate": metrics.recovery_success_rate,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.warning(
            f"Health alert for workflow {workflow_id}: {health_status.value} - "
            f"Error rate: {metrics.error_rate:.2%}, "
            f"Consecutive failures: {metrics.consecutive_failures}, "
            f"Recovery success rate: {metrics.recovery_success_rate:.2%}"
        )
        
        # Here you could integrate with alerting systems like:
        # - Send to monitoring dashboard
        # - Send email/SMS alerts
        # - Trigger automated remediation
        # - Log to external monitoring service
    
    def get_workflow_health(self, workflow_id: str) -> Optional[Tuple[HealthStatus, HealthMetrics]]:
        """
        Get current health status and metrics for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Tuple of health status and metrics, or None if not found
        """
        if workflow_id not in self.health_metrics:
            return None
        
        metrics = self.health_metrics[workflow_id]
        health_status = self._assess_workflow_health(workflow_id, metrics)
        return health_status, metrics
    
    def get_failure_patterns(self, workflow_id: Optional[str] = None) -> Dict[FailurePattern, int]:
        """
        Get failure pattern distribution.
        
        Args:
            workflow_id: Optional workflow ID to filter by
            
        Returns:
            Dictionary of failure patterns and their counts
        """
        events = self.failure_events
        if workflow_id:
            events = [e for e in events if e.workflow_id == workflow_id]
        
        pattern_counts = {}
        for pattern in FailurePattern:
            pattern_counts[pattern] = len([
                e for e in events if e.failure_pattern == pattern
            ])
        
        return pattern_counts
    
    def should_trigger_intervention(self, workflow_id: str) -> bool:
        """
        Determine if manual intervention is needed.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            True if intervention is recommended
        """
        health_data = self.get_workflow_health(workflow_id)
        if not health_data:
            return False
        
        health_status, metrics = health_data
        
        # Trigger intervention for critical status or repeated recovery failures
        return (health_status == HealthStatus.CRITICAL or
                (metrics.consecutive_failures >= 5 and 
                 metrics.recovery_success_rate <= 0.3))
    
    def get_health_summary(self) -> Dict:
        """
        Get overall health summary for all workflows.
        
        Returns:
            Dictionary containing health summary
        """
        total_workflows = len(self.health_metrics)
        if total_workflows == 0:
            return {
                "total_workflows": 0,
                "healthy": 0,
                "degraded": 0,
                "critical": 0,
                "recovering": 0,
                "overall_health": "unknown"
            }
        
        status_counts = {status: 0 for status in HealthStatus}
        
        for workflow_id, metrics in self.health_metrics.items():
            status = self._assess_workflow_health(workflow_id, metrics)
            status_counts[status] += 1
        
        # Determine overall health
        if status_counts[HealthStatus.CRITICAL] > 0:
            overall_health = "critical"
        elif status_counts[HealthStatus.DEGRADED] > total_workflows * 0.3:
            overall_health = "degraded"
        elif status_counts[HealthStatus.RECOVERING] > 0:
            overall_health = "recovering"
        else:
            overall_health = "healthy"
        
        return {
            "total_workflows": total_workflows,
            "healthy": status_counts[HealthStatus.HEALTHY],
            "degraded": status_counts[HealthStatus.DEGRADED],
            "critical": status_counts[HealthStatus.CRITICAL],
            "recovering": status_counts[HealthStatus.RECOVERING],
            "overall_health": overall_health,
            "total_failure_events": len(self.failure_events)
        }
