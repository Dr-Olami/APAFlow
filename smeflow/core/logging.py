"""
SMEFlow logging configuration.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.typing import FilteringBoundLogger

from smeflow.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for SMEFlow.
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.DEBUG else logging.INFO
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__).
        
    Returns:
        FilteringBoundLogger: Configured logger instance.
    """
    return structlog.get_logger(name)


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    tenant_id: str = None,
    **kwargs: Any
) -> None:
    """
    Log HTTP request with structured data.
    
    Args:
        method: HTTP method.
        path: Request path.
        status_code: Response status code.
        duration_ms: Request duration in milliseconds.
        tenant_id: Tenant ID if available.
        **kwargs: Additional context.
    """
    logger = get_logger("smeflow.request")
    
    context = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        **kwargs
    }
    
    if tenant_id:
        context["tenant_id"] = tenant_id
    
    logger.info("HTTP request", **context)


def log_agent_execution(
    agent_id: str,
    agent_type: str,
    action: str,
    duration_ms: float,
    tenant_id: str,
    success: bool = True,
    **kwargs: Any
) -> None:
    """
    Log agent execution with structured data.
    
    Args:
        agent_id: Agent identifier.
        agent_type: Type of agent (automator, mentor, supervisor).
        action: Action performed.
        duration_ms: Execution duration in milliseconds.
        tenant_id: Tenant ID.
        success: Whether execution was successful.
        **kwargs: Additional context.
    """
    logger = get_logger("smeflow.agent")
    
    context = {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "action": action,
        "duration_ms": duration_ms,
        "tenant_id": tenant_id,
        "success": success,
        **kwargs
    }
    
    if success:
        logger.info("Agent execution completed", **context)
    else:
        logger.error("Agent execution failed", **context)


def log_llm_usage(
    provider: str,
    model: str,
    tokens_used: int,
    cost_usd: float,
    tenant_id: str,
    **kwargs: Any
) -> None:
    """
    Log LLM usage for cost tracking.
    
    Args:
        provider: LLM provider (openai, anthropic, etc.).
        model: Model name.
        tokens_used: Number of tokens consumed.
        cost_usd: Cost in USD.
        tenant_id: Tenant ID.
        **kwargs: Additional context.
    """
    logger = get_logger("smeflow.llm")
    
    logger.info(
        "LLM usage",
        provider=provider,
        model=model,
        tokens_used=tokens_used,
        cost_usd=cost_usd,
        tenant_id=tenant_id,
        **kwargs
    )
