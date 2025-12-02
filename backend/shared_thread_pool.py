"""
Shared Thread Pool Manager for Horizontal Scaling
Prevents resource waste by reusing thread pools across instances
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable, List, Any
from dataclasses import dataclass

@dataclass
class ThreadPoolStats:
    """Thread pool statistics"""
    max_workers: int
    active_threads: int
    queued_tasks: int
    completed_tasks: int


class SharedThreadPoolManager:
    """
    Shared thread pool manager that prevents resource waste
    Reuses thread pools instead of creating new ones per request
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize shared thread pool manager
        
        Args:
            max_workers: Maximum number of worker threads (default: CPU count * 2)
        """
        if max_workers is None:
            # Auto-detect optimal worker count
            cpu_count = os.cpu_count() or 4
            max_workers = min(cpu_count * 2, 10)  # Max 10 workers to prevent resource exhaustion
        
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._completed_tasks = 0
        self._lock = threading.Lock()
        
        print(f"✅ Shared thread pool initialized with {max_workers} workers")
    
    def submit(self, fn: Callable, *args, **kwargs):
        """
        Submit a task to the thread pool
        
        Args:
            fn: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Future object
        """
        future = self._executor.submit(fn, *args, **kwargs)
        
        # Track completed tasks
        def on_complete(f):
            with self._lock:
                self._completed_tasks += 1
        
        future.add_done_callback(on_complete)
        return future
    
    def map(self, fn: Callable, iterable, timeout: Optional[float] = None):
        """
        Map function over iterable using thread pool
        
        Args:
            fn: Function to execute
            iterable: Items to process
            timeout: Maximum time to wait for results
            
        Returns:
            Iterator of results
        """
        return self._executor.map(fn, iterable, timeout=timeout)
    
    def execute_batch(self, tasks: List[tuple[Callable, tuple, dict]], 
                      timeout: Optional[float] = None) -> List[Any]:
        """
        Execute batch of tasks in parallel
        
        Args:
            tasks: List of (function, args, kwargs) tuples
            timeout: Maximum time to wait for all tasks
            
        Returns:
            List of results (same order as tasks)
        """
        futures = []
        for fn, args, kwargs in tasks:
            future = self.submit(fn, *args, **kwargs)
            futures.append(future)
        
        results = []
        for future in as_completed(futures, timeout=timeout):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({'error': str(e)})
        
        return results
    
    def get_stats(self) -> ThreadPoolStats:
        """
        Get thread pool statistics
        
        Returns:
            ThreadPoolStats object
        """
        # ThreadPoolExecutor doesn't expose queue size, so we approximate
        return ThreadPoolStats(
            max_workers=self.max_workers,
            active_threads=threading.active_count() - 1,  # Subtract main thread
            queued_tasks=0,  # Not available in ThreadPoolExecutor
            completed_tasks=self._completed_tasks
        )
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown thread pool
        
        Args:
            wait: Wait for pending tasks to complete
        """
        print(f"🛑 Shutting down thread pool (completed {self._completed_tasks} tasks)")
        self._executor.shutdown(wait=wait)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown(wait=True)


# Singleton instance
_thread_pool_instance = None
_thread_pool_lock = threading.Lock()


def get_thread_pool(max_workers: Optional[int] = None) -> SharedThreadPoolManager:
    """
    Get singleton thread pool instance
    Thread-safe singleton creation
    
    Args:
        max_workers: Maximum workers (only used on first call)
        
    Returns:
        SharedThreadPoolManager instance
    """
    global _thread_pool_instance
    
    if _thread_pool_instance is None:
        with _thread_pool_lock:
            # Double-check locking pattern
            if _thread_pool_instance is None:
                _thread_pool_instance = SharedThreadPoolManager(max_workers)
    
    return _thread_pool_instance


def parallel_execute(functions: List[Callable], *args_list, timeout: Optional[float] = None) -> List[Any]:
    """
    Helper function to execute multiple functions in parallel using shared pool
    
    Args:
        functions: List of functions to execute
        *args_list: Arguments for each function (must match length of functions)
        timeout: Maximum time to wait
        
    Returns:
        List of results
    """
    thread_pool = get_thread_pool()
    
    tasks = []
    for i, fn in enumerate(functions):
        args = args_list[i] if i < len(args_list) else ()
        tasks.append((fn, args, {}))
    
    return thread_pool.execute_batch(tasks, timeout=timeout)


# Cleanup on module unload
import atexit

def _cleanup_thread_pool():
    """Cleanup thread pool on exit"""
    global _thread_pool_instance
    if _thread_pool_instance:
        _thread_pool_instance.shutdown(wait=False)

atexit.register(_cleanup_thread_pool)
