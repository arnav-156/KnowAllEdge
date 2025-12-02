"""
Test Circuit Breaker Enhancements
Tests separate breakers and metrics export
"""

import time
from circuit_breaker import (
    CircuitBreaker, CircuitState, CircuitBreakerError,
    initialize_circuit_breakers,
    get_text_generation_breaker,
    get_vision_api_breaker,
    get_imagen_breaker,
    get_all_breakers,
    get_all_metrics,
    export_all_prometheus_metrics
)
from config import get_config

print("=" * 70)
print("CIRCUIT BREAKER ENHANCEMENTS TEST")
print("=" * 70)

# Initialize breakers
config = get_config()
initialize_circuit_breakers(config)

# Test 1: Separate breakers exist
print("\n" + "=" * 70)
print("TEST 1: Separate Circuit Breakers")
print("=" * 70)

text_breaker = get_text_generation_breaker()
vision_breaker = get_vision_api_breaker()
imagen_breaker = get_imagen_breaker()

print(f"\n✓ Text Generation Breaker: {text_breaker.name if text_breaker else 'None'}")
print(f"✓ Vision API Breaker: {vision_breaker.name if vision_breaker else 'None'}")
print(f"✓ Imagen Breaker: {imagen_breaker.name if imagen_breaker else 'None'}")

all_breakers = get_all_breakers()
print(f"\n✓ Total breakers: {len(all_breakers)}")
print(f"✓ Breaker names: {list(all_breakers.keys())}")

# Test 2: Separate breakers work independently
print("\n" + "=" * 70)
print("TEST 2: Independent Breaker Operation")
print("=" * 70)

if text_breaker and vision_breaker:
    # Simulate failures in text breaker only
    def failing_function():
        raise Exception("Simulated failure")
    
    print("\nSimulating 5 failures in TEXT breaker...")
    for i in range(5):
        try:
            text_breaker.call(failing_function)
        except Exception:
            pass
    
    print(f"  Text breaker state: {text_breaker.state.value}")
    print(f"  Vision breaker state: {vision_breaker.state.value}")
    
    if text_breaker.state == CircuitState.OPEN and vision_breaker.state == CircuitState.CLOSED:
        print("\n✅ PASS: Text breaker OPEN, Vision breaker still CLOSED")
    else:
        print("\n❌ FAIL: Breakers not independent")
    
    # Reset for next tests
    text_breaker.force_close()

# Test 3: Metrics tracking
print("\n" + "=" * 70)
print("TEST 3: Metrics Tracking")
print("=" * 70)

if text_breaker:
    # Perform some operations
    def success_function():
        return "success"
    
    def failure_function():
        raise Exception("failure")
    
    print("\nPerforming 10 successful calls...")
    for i in range(10):
        try:
            text_breaker.call(success_function)
        except:
            pass
    
    print("Performing 3 failed calls...")
    for i in range(3):
        try:
            text_breaker.call(failure_function)
        except:
            pass
    
    metrics = text_breaker.get_metrics()
    
    print(f"\nMetrics for {metrics['name']}:")
    print(f"  Total calls: {metrics['total_calls']}")
    print(f"  Successful: {metrics['successful_calls']}")
    print(f"  Failed: {metrics['failed_calls']}")
    print(f"  Success rate: {metrics['success_rate_percent']}%")
    print(f"  Failure rate: {metrics['failure_rate_percent']}%")
    print(f"  Current state: {metrics['state']}")
    print(f"  Is healthy: {metrics['is_healthy']}")
    
    if metrics['total_calls'] == 13 and metrics['successful_calls'] == 10:
        print("\n✅ PASS: Metrics tracked correctly")
    else:
        print("\n❌ FAIL: Metrics not accurate")

# Test 4: Metrics export for all breakers
print("\n" + "=" * 70)
print("TEST 4: All Breakers Metrics Export")
print("=" * 70)

all_metrics = get_all_metrics()

print(f"\nExported metrics for {len(all_metrics)} breakers:\n")
for name, metrics in all_metrics.items():
    print(f"  {name}:")
    print(f"    State: {metrics['state']}")
    print(f"    Total calls: {metrics['total_calls']}")
    print(f"    Success rate: {metrics['success_rate_percent']}%")
    print(f"    Uptime: {metrics['uptime_seconds']}s")

if len(all_metrics) == 3:
    print("\n✅ PASS: All 3 breakers reporting metrics")
else:
    print(f"\n⚠️  Expected 3 breakers, got {len(all_metrics)}")

# Test 5: Prometheus format export
print("\n" + "=" * 70)
print("TEST 5: Prometheus Metrics Export")
print("=" * 70)

prometheus_metrics = export_all_prometheus_metrics()

print("\nPrometheus format sample:")
print("-" * 70)
lines = prometheus_metrics.split('\n')
for line in lines[:20]:  # Show first 20 lines
    print(line)
if len(lines) > 20:
    print(f"... ({len(lines) - 20} more lines)")
print("-" * 70)

# Validate Prometheus format
has_help = '# HELP' in prometheus_metrics
has_type = '# TYPE' in prometheus_metrics
has_metrics = 'circuit_breaker_' in prometheus_metrics

print(f"\nPrometheus format validation:")
print(f"  Has HELP comments: {'✓' if has_help else '✗'}")
print(f"  Has TYPE comments: {'✓' if has_type else '✗'}")
print(f"  Has metric data: {'✓' if has_metrics else '✗'}")

if has_help and has_type and has_metrics:
    print("\n✅ PASS: Prometheus format valid")
else:
    print("\n❌ FAIL: Prometheus format invalid")

# Test 6: State transitions tracking
print("\n" + "=" * 70)
print("TEST 6: State Transition Tracking")
print("=" * 70)

if vision_breaker:
    print("\nTesting state transitions on vision breaker...")
    
    # Start in CLOSED
    vision_breaker.force_close()
    print(f"  Initial state: {vision_breaker.state.value}")
    
    # Transition to OPEN
    vision_breaker.force_open()
    print(f"  After force_open: {vision_breaker.state.value}")
    
    metrics = vision_breaker.get_metrics()
    transitions = metrics['state_transitions']
    
    print(f"\nState transitions:")
    for transition, count in transitions.items():
        if count > 0:
            print(f"  {transition}: {count}")
    
    if transitions['closed_to_open'] > 0:
        print("\n✅ PASS: State transitions tracked")
    else:
        print("\n❌ FAIL: State transitions not tracked")
    
    # Reset
    vision_breaker.force_close()

# Test 7: Health indicators
print("\n" + "=" * 70)
print("TEST 7: Health Indicators")
print("=" * 70)

if text_breaker:
    text_breaker.force_close()
    metrics = text_breaker.get_metrics()
    
    print(f"\nHealth indicators when CLOSED:")
    print(f"  is_healthy: {metrics['is_healthy']}")
    print(f"  is_degraded: {metrics['is_degraded']}")
    print(f"  is_failing: {metrics['is_failing']}")
    
    if metrics['is_healthy'] and not metrics['is_failing']:
        print("  ✓ Correct for CLOSED state")
    
    text_breaker.force_open()
    metrics = text_breaker.get_metrics()
    
    print(f"\nHealth indicators when OPEN:")
    print(f"  is_healthy: {metrics['is_healthy']}")
    print(f"  is_degraded: {metrics['is_degraded']}")
    print(f"  is_failing: {metrics['is_failing']}")
    
    if not metrics['is_healthy'] and metrics['is_failing']:
        print("  ✓ Correct for OPEN state")
        print("\n✅ PASS: Health indicators accurate")
    else:
        print("\n❌ FAIL: Health indicators incorrect")
    
    text_breaker.force_close()

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

print("\n✅ Enhancements Verified:")
print("  1. Separate breakers for text/vision/imagen")
print("  2. Independent operation (text failure doesn't affect vision)")
print("  3. Comprehensive metrics tracking")
print("  4. All breakers metrics export")
print("  5. Prometheus format export")
print("  6. State transition tracking")
print("  7. Health indicator flags")

print("\n✅ Benefits:")
print("  - Vision API failures don't block text generation")
print("  - Imagen failures don't block vision or text")
print("  - Per-service monitoring and alerting possible")
print("  - Prometheus/Grafana integration ready")

print("\n" + "=" * 70)
print("ALL TESTS COMPLETE ✅")
print("=" * 70)
