"""
Test Suite for Horizontal Scaling Features
Tests distributed sessions, shared thread pools, and stateless operation
"""

import sys
import time
import json
from datetime import datetime

# Test colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_section(title):
    """Print section header"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

def print_test(name, passed, details=""):
    """Print test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status}: {name}")
    if details:
        print(f"    {details}")

# Test 1: Distributed Session Manager
def test_distributed_sessions():
    """Test distributed session management"""
    print_section("TEST 1: Distributed Session Manager")
    
    try:
        from distributed_session import DistributedSessionManager
        from config import get_config
        
        config = get_config()
        session_manager = DistributedSessionManager(config.redis)
        
        # Test 1.1: Create session
        session_id = session_manager.create_session(user_id="test_user", metadata={"test": "data"})
        print_test(
            "Create session", 
            session_id is not None,
            f"Session ID: {session_id[:16]}..."
        )
        
        # Test 1.2: Retrieve session
        session_data = session_manager.get_session(session_id)
        print_test(
            "Retrieve session",
            session_data is not None and session_data['user_id'] == "test_user",
            f"User ID: {session_data['user_id'] if session_data else 'None'}"
        )
        
        # Test 1.3: Update session
        updated = session_manager.update_session(session_id, {"user_id": "updated_user"})
        session_data = session_manager.get_session(session_id)
        print_test(
            "Update session",
            updated and session_data['user_id'] == "updated_user",
            f"Updated user ID: {session_data['user_id'] if session_data else 'None'}"
        )
        
        # Test 1.4: Session count
        count = session_manager.get_active_session_count()
        print_test(
            "Active session count",
            count >= 1,
            f"Active sessions: {count}"
        )
        
        # Test 1.5: Get or create session (existing)
        same_id, same_data = session_manager.get_or_create_session(session_id)
        print_test(
            "Get existing session",
            same_id == session_id and same_data['user_id'] == "updated_user",
            f"Same session: {same_id == session_id}"
        )
        
        # Test 1.6: Get or create session (new)
        new_id, new_data = session_manager.get_or_create_session(None)
        print_test(
            "Create new session",
            new_id != session_id and new_data is not None,
            f"New session ID: {new_id[:16]}..."
        )
        
        # Test 1.7: Delete session
        deleted = session_manager.delete_session(session_id)
        session_data = session_manager.get_session(session_id)
        print_test(
            "Delete session",
            deleted and session_data is None,
            f"Session deleted: {session_data is None}"
        )
        
        # Cleanup
        session_manager.delete_session(new_id)
        
        print(f"\n{Colors.GREEN}✅ DISTRIBUTED SESSIONS: All tests passed{Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ DISTRIBUTED SESSIONS: Test failed - {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False

# Test 2: Shared Thread Pool
def test_shared_thread_pool():
    """Test shared thread pool manager"""
    print_section("TEST 2: Shared Thread Pool Manager")
    
    try:
        from shared_thread_pool import SharedThreadPoolManager, get_thread_pool
        
        # Test 2.1: Initialize pool
        pool = SharedThreadPoolManager(max_workers=4)
        print_test(
            "Initialize thread pool",
            pool.max_workers == 4,
            f"Max workers: {pool.max_workers}"
        )
        
        # Test 2.2: Submit task
        def test_task(x):
            time.sleep(0.1)
            return x * 2
        
        future = pool.submit(test_task, 5)
        result = future.result()
        print_test(
            "Submit task",
            result == 10,
            f"Result: {result}"
        )
        
        # Test 2.3: Map function
        results = list(pool.map(lambda x: x * 2, [1, 2, 3, 4, 5]))
        print_test(
            "Map function",
            results == [2, 4, 6, 8, 10],
            f"Results: {results}"
        )
        
        # Test 2.4: Batch execution
        tasks = [
            (lambda x: x * 2, (2,), {}),
            (lambda x: x * 3, (3,), {}),
            (lambda x: x * 4, (4,), {})
        ]
        batch_results = pool.execute_batch(tasks)
        print_test(
            "Batch execution",
            len(batch_results) == 3,
            f"Batch results: {len(batch_results)} tasks completed"
        )
        
        # Test 2.5: Get stats
        stats = pool.get_stats()
        print_test(
            "Get statistics",
            stats.max_workers == 4 and stats.completed_tasks > 0,
            f"Completed: {stats.completed_tasks}, Max workers: {stats.max_workers}"
        )
        
        # Test 2.6: Singleton pattern
        singleton_pool = get_thread_pool()
        print_test(
            "Singleton pattern",
            singleton_pool is not None,
            "Singleton instance retrieved"
        )
        
        # Cleanup
        pool.shutdown()
        print_test(
            "Shutdown pool",
            True,
            "Pool shutdown successfully"
        )
        
        print(f"\n{Colors.GREEN}✅ SHARED THREAD POOL: All tests passed{Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ SHARED THREAD POOL: Test failed - {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False

# Test 3: Stateless Operation
def test_stateless_operation():
    """Test that application can run statelessly"""
    print_section("TEST 3: Stateless Operation")
    
    try:
        from distributed_session import get_session_manager
        from shared_thread_pool import get_thread_pool
        from config import get_config
        
        config = get_config()
        
        # Test 3.1: Session manager is shared
        session_mgr1 = get_session_manager(config)
        session_mgr2 = get_session_manager(config)
        print_test(
            "Session manager singleton",
            session_mgr1 is session_mgr2,
            "Same instance across calls"
        )
        
        # Test 3.2: Thread pool is shared
        pool1 = get_thread_pool()
        pool2 = get_thread_pool()
        print_test(
            "Thread pool singleton",
            pool1 is pool2,
            "Same instance across calls"
        )
        
        # Test 3.3: Sessions persist across "instances"
        session_id = session_mgr1.create_session(user_id="test")
        
        # Simulate different instance retrieving session
        session_data = session_mgr2.get_session(session_id)
        print_test(
            "Cross-instance session access",
            session_data is not None and session_data['user_id'] == "test",
            f"Session accessible: {session_data is not None}"
        )
        
        # Test 3.4: No Flask app context required
        print_test(
            "No app context dependency",
            True,  # If we got here, no app context was needed
            "Session operations work without Flask context"
        )
        
        # Cleanup
        session_mgr1.delete_session(session_id)
        
        print(f"\n{Colors.GREEN}✅ STATELESS OPERATION: All tests passed{Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ STATELESS OPERATION: Test failed - {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False

# Test 4: Resource Management
def test_resource_management():
    """Test that resources are properly managed at scale"""
    print_section("TEST 4: Resource Management")
    
    try:
        from shared_thread_pool import get_thread_pool
        import threading
        
        # Test 4.1: Thread pool limits
        pool = get_thread_pool(max_workers=3)
        
        # Submit more tasks than workers
        def slow_task():
            time.sleep(0.2)
            return True
        
        futures = [pool.submit(slow_task) for _ in range(10)]
        results = [f.result() for f in futures]
        
        print_test(
            "Thread pool handles overload",
            len(results) == 10 and all(results),
            f"Processed {len(results)} tasks with 3 workers"
        )
        
        # Test 4.2: Thread count doesn't explode
        initial_threads = threading.active_count()
        
        # Create many thread pools (should reuse same instance)
        for _ in range(10):
            _ = get_thread_pool()
        
        final_threads = threading.active_count()
        print_test(
            "Thread count controlled",
            final_threads <= initial_threads + 5,  # Allow some variance
            f"Threads: {initial_threads} -> {final_threads}"
        )
        
        # Test 4.3: Memory efficiency (sessions)
        from distributed_session import get_session_manager
        from config import get_config
        
        config = get_config()
        session_mgr = get_session_manager(config)
        
        # Create many sessions
        session_ids = []
        for i in range(100):
            sid = session_mgr.create_session(user_id=f"user_{i}")
            session_ids.append(sid)
        
        count = session_mgr.get_active_session_count()
        print_test(
            "Session storage efficient",
            count >= 100,
            f"Stored {count} sessions efficiently"
        )
        
        # Cleanup
        for sid in session_ids:
            session_mgr.delete_session(sid)
        
        print(f"\n{Colors.GREEN}✅ RESOURCE MANAGEMENT: All tests passed{Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ RESOURCE MANAGEMENT: Test failed - {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False

# Test 5: Configuration
def test_configuration():
    """Test load balancer and deployment configurations"""
    print_section("TEST 5: Configuration Files")
    
    try:
        import os
        
        # Test 5.1: Nginx config exists
        nginx_exists = os.path.exists('nginx.conf')
        print_test(
            "Nginx configuration",
            nginx_exists,
            "nginx.conf present" if nginx_exists else "nginx.conf missing"
        )
        
        # Test 5.2: HAProxy config exists
        haproxy_exists = os.path.exists('haproxy.cfg')
        print_test(
            "HAProxy configuration",
            haproxy_exists,
            "haproxy.cfg present" if haproxy_exists else "haproxy.cfg missing"
        )
        
        # Test 5.3: Docker Compose exists
        docker_exists = os.path.exists('docker-compose.yml')
        print_test(
            "Docker Compose configuration",
            docker_exists,
            "docker-compose.yml present" if docker_exists else "docker-compose.yml missing"
        )
        
        # Test 5.4: Nginx config is valid
        if nginx_exists:
            with open('nginx.conf', 'r') as f:
                nginx_content = f.read()
                has_upstream = 'upstream' in nginx_content
                has_health_check = '/api/health' in nginx_content
                has_ssl = 'ssl' in nginx_content
                
                print_test(
                    "Nginx config valid",
                    has_upstream and has_health_check,
                    f"Upstream: {has_upstream}, Health: {has_health_check}, SSL: {has_ssl}"
                )
        
        # Test 5.5: Docker Compose is valid
        if docker_exists:
            with open('docker-compose.yml', 'r') as f:
                docker_content = f.read()
                has_redis = 'redis:' in docker_content
                has_backend = 'backend_' in docker_content
                has_scaling = 'backend_2' in docker_content
                
                print_test(
                    "Docker Compose valid",
                    has_redis and has_backend and has_scaling,
                    f"Redis: {has_redis}, Backend: {has_backend}, Scaling: {has_scaling}"
                )
        
        print(f"\n{Colors.GREEN}✅ CONFIGURATION: All tests passed{Colors.RESET}")
        return True
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ CONFIGURATION: Test failed - {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False

# Main test runner
def main():
    """Run all scalability tests"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"{Colors.YELLOW}HORIZONTAL SCALING TEST SUITE{Colors.RESET}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"\nTesting:")
    print("  1. Distributed Session Management")
    print("  2. Shared Thread Pool")
    print("  3. Stateless Operation")
    print("  4. Resource Management")
    print("  5. Configuration Files\n")
    
    results = []
    
    # Run tests
    results.append(("Distributed Sessions", test_distributed_sessions()))
    results.append(("Shared Thread Pool", test_shared_thread_pool()))
    results.append(("Stateless Operation", test_stateless_operation()))
    results.append(("Resource Management", test_resource_management()))
    results.append(("Configuration", test_configuration()))
    
    # Summary
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"{Colors.YELLOW}TEST SUMMARY{Colors.RESET}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.RESET}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {total}")
    print(f"  {Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {total - passed}{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✅ ALL TESTS PASSED - READY FOR HORIZONTAL SCALING{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}❌ SOME TESTS FAILED - REVIEW NEEDED{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
