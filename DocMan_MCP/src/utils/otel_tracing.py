from functools import wraps
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
import inspect
from fastapi import Request

def traced_function(span_name=None):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(func.__module__)
            name = span_name or func.__name__
            session_id = None
            # Try to extract session_id from kwargs, class, or FastAPI request headers
            if 'session_id' in kwargs:
                session_id = kwargs['session_id']
            elif args and hasattr(args[0], 'session_id'):
                session_id = getattr(args[0], 'session_id')
            # Check for FastAPI Request in args or kwargs
            request = None
            for arg in list(args) + list(kwargs.values()):
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is not None:
                session_id = session_id or request.headers.get('x-session-id')
            with tracer.start_as_current_span(name) as span:
                # Add function arguments as span attributes
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                for k, v in bound.arguments.items():
                    try:
                        span.set_attribute(k, str(v))
                    except Exception:
                        pass
                if session_id:
                    span.set_attribute('session_id', str(session_id))
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(func.__module__)
            name = span_name or func.__name__
            session_id = None
            if 'session_id' in kwargs:
                session_id = kwargs['session_id']
            elif args and hasattr(args[0], 'session_id'):
                session_id = getattr(args[0], 'session_id')
            request = None
            for arg in list(args) + list(kwargs.values()):
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is not None:
                session_id = session_id or request.headers.get('x-session-id')
            with tracer.start_as_current_span(name) as span:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                for k, v in bound.arguments.items():
                    try:
                        span.set_attribute(k, str(v))
                    except Exception:
                        pass
                if session_id:
                    span.set_attribute('session_id', str(session_id))
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator
