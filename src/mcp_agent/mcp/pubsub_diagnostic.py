"""
Diagnostic module for PubSub integration.

This module provides logging and diagnostic functions to help identify 
integration points and message flow through the system.
"""

import functools
import inspect
import logging
from typing import Any, Callable, Optional, TypeVar, cast

from mcp_agent.logging.logger import get_logger

logger = get_logger(__name__, level=logging.DEBUG)

# Type variables for function annotations
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])


def log_call(func: F) -> F:
    """
    Decorator that logs function calls with parameters.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__qualname__
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        
        logger.debug(f"CALL: {func_name}({signature})")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"RETURN: {func_name} -> {type(result).__name__}")
            return result
        except Exception as e:
            logger.error(f"EXCEPTION in {func_name}: {type(e).__name__}: {e}")
            raise
    
    return cast(F, wrapper)


def log_async_call(func: AsyncF) -> AsyncF:
    """
    Decorator that logs asynchronous function calls with parameters.
    
    Args:
        func: Asynchronous function to decorate
        
    Returns:
        Decorated asynchronous function
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__qualname__
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        
        logger.debug(f"ASYNC CALL: {func_name}({signature})")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"ASYNC RETURN: {func_name} -> {type(result).__name__}")
            return result
        except Exception as e:
            logger.error(f"ASYNC EXCEPTION in {func_name}: {type(e).__name__}: {e}")
            raise
    
    return cast(AsyncF, wrapper)


def get_caller_info() -> str:
    """
    Get information about the caller of the current function.
    
    Returns:
        String with caller information
    """
    stack = inspect.stack()
    # Skip the current function and get the caller
    frame_info = stack[2] if len(stack) > 2 else stack[1]
    
    function_name = frame_info.function
    filename = frame_info.filename
    lineno = frame_info.lineno
    
    return f"{filename}:{lineno} in {function_name}"


def log_message_flow(message: Any, source: Optional[str] = None) -> None:
    """
    Log a message flowing through the system.
    
    Args:
        message: The message being passed
        source: Optional source of the message
    """
    caller = get_caller_info()
    source_info = f" from {source}" if source else ""
    
    logger.debug(
        f"MESSAGE FLOW{source_info} at {caller}: {type(message).__name__}",
        extra={"message_type": type(message).__name__}
    )


def instrument_key_components() -> None:
    """
    Add instrumentation to key components for diagnostics.
    """
    # Import components that need instrumentation
    from mcp_agent.ui.console_display import ConsoleDisplay
    from mcp_agent.core.fastagent import FastAgent
    from mcp_agent.mcp.mcp_aggregator import MCPAggregator
    
    # Instrument ConsoleDisplay methods
    ConsoleDisplay.show_assistant_message = log_async_call(ConsoleDisplay.show_assistant_message)
    ConsoleDisplay.show_user_message = log_call(ConsoleDisplay.show_user_message)
    ConsoleDisplay.show_tool_result = log_call(ConsoleDisplay.show_tool_result)
    ConsoleDisplay.show_tool_call = log_call(ConsoleDisplay.show_tool_call)
    
    # Instrument FastAgent methods
    FastAgent.run = log_async_call(FastAgent.run)
    
    # Instrument MCPAggregator methods
    MCPAggregator.call_tool = log_async_call(MCPAggregator.call_tool)
    
    logger.info("Key components instrumented for diagnostics")