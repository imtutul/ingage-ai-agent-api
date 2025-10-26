#!/usr/bin/env python3
"""
Enhanced error handling and retry logic for fabric data agent
"""

import time
import functools
from typing import Callable, Any

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function calls on failure with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        print(f"✅ Function {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                    
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Don't retry on certain types of errors
                    if any(term in error_msg for term in ['401', 'unauthorized', '403', 'forbidden', 'authentication']):
                        print(f"❌ {func.__name__} failed with auth error (no retry): {e}")
                        raise e
                    
                    if attempt < max_retries:
                        print(f"⚠️ {func.__name__} failed on attempt {attempt + 1}/{max_retries + 1}: {e}")
                        print(f"🔄 Retrying in {current_delay:.1f} seconds...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        print(f"❌ {func.__name__} failed after {max_retries + 1} attempts")
            
            # If we get here, all retries failed
            raise last_exception
            
        return wrapper
    return decorator

def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable"""
    error_msg = str(error).lower()
    
    # Don't retry authentication errors
    if any(term in error_msg for term in ['401', 'unauthorized', '403', 'forbidden']):
        return False
    
    # Don't retry validation errors  
    if any(term in error_msg for term in ['400', 'bad request', 'invalid']):
        return False
    
    # Retry on these types of errors
    retryable_terms = [
        '500', '500: internal server error',
        '502', '502: bad gateway', 
        '503', '503: service unavailable',
        '504', '504: gateway timeout',
        'timeout', 'timed out',
        'connection', 'network',
        'rate limit', '429'
    ]
    
    return any(term in error_msg for term in retryable_terms)

# Example usage:
# @retry_on_failure(max_retries=2, delay=1.0)
# def some_api_call():
#     # Your API call here
#     pass