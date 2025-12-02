"""
Performance Implementation Validation Script
Validates all Phase 12 performance features are working correctly
"""

import os
import sys
import tempfile
from PIL import Image

print("=" * 80)
print("Performance Optimization Implementation Validation")
print("=" * 80)
print()

# Test 1: Import all modules
print("1. Testing module imports...")
try:
    from cdn_manager import CDNManager, AssetOptimizer
    from image_optimizer import ImageOptimizer, LazyLoadingHelper
    from connection_pool_optimizer import ConnectionPoolOptimizer, ConnectionPoolMonitor
    print("   ✓ All modules imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: CDN Manager
print("\n2. Testing CDN Manager...")
try:
    cdn = CDNManager(cdn_url='https://cdn.example.com', enable_minification=True)
    
    # Test URL generation
    url = cdn.get_cdn_url('/static/js/app.js', version='1.0.0')
    assert 'cdn.example.com' in url
    assert 'v=1.0.0' in url
    
    # Test cache headers
    headers = cdn.get_cache_headers('/static/images/logo.jpg')
    assert 'Cache-Control' in headers
    assert 'max-age=31536000' in headers['Cache-Control']
    
    print("   ✓ CDN Manager working correctly")
except Exception as e:
    print(f"   ✗ CDN Manager test failed: {e}")
    sys.exit(1)

# Test 3: Asset Optimizer
print("\n3. Testing Asset Optimizer...")
try:
    css = "/* Comment */ body { margin: 0; }"
    minified = AssetOptimizer.minify_css(css)
    
    assert len(minified) < len(css)
    assert '/*' not in minified
    
    ratio = AssetOptimizer.calculate_compression_ratio(1000, 500)
    assert ratio == 0.5
    
    print("   ✓ Asset Optimizer working correctly")
except Exception as e:
    print(f"   ✗ Asset Optimizer test failed: {e}")
    sys.exit(1)

# Test 4: Image Optimizer
print("\n4. Testing Image Optimizer...")
try:
    optimizer = ImageOptimizer(quality=85, max_width=1024, max_height=1024)
    
    # Create test image
    img = Image.new('RGB', (800, 600), color='red')
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, 'JPEG', quality=100)
        temp_path = f.name
    
    try:
        # Optimize
        result = optimizer.optimize_image(temp_path, target_format='JPEG')
        assert result['success'] is True
        assert os.path.exists(result['output_path'])
        
        # Cleanup
        if os.path.exists(result['output_path']):
            os.unlink(result['output_path'])
        
        print("   ✓ Image Optimizer working correctly")
    finally:
        os.unlink(temp_path)
        
except Exception as e:
    print(f"   ✗ Image Optimizer test failed: {e}")
    sys.exit(1)

# Test 5: WebP Conversion
print("\n5. Testing WebP Conversion...")
try:
    optimizer = ImageOptimizer()
    
    img = Image.new('RGB', (100, 100), color='blue')
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, 'JPEG')
        temp_path = f.name
    
    try:
        result = optimizer.convert_to_webp(temp_path)
        assert result['success'] is True
        assert result['output_format'] == 'WEBP'
        
        # Cleanup
        if os.path.exists(result['output_path']):
            os.unlink(result['output_path'])
        
        print("   ✓ WebP Conversion working correctly")
    finally:
        os.unlink(temp_path)
        
except Exception as e:
    print(f"   ✗ WebP Conversion test failed: {e}")
    sys.exit(1)

# Test 6: Lazy Loading
print("\n6. Testing Lazy Loading...")
try:
    img_tag = LazyLoadingHelper.generate_img_tag(
        src='/images/test.jpg',
        alt='Test',
        width=800,
        height=600,
        lazy=True
    )
    
    assert 'loading="lazy"' in img_tag
    assert 'src="/images/test.jpg"' in img_tag
    
    sources = [
        {'srcset': '/images/test.webp', 'type': 'image/webp'},
        {'srcset': '/images/test.jpg', 'type': 'image/jpeg'}
    ]
    picture_tag = LazyLoadingHelper.generate_picture_tag(
        sources=sources,
        fallback_src='/images/test.jpg',
        alt='Test',
        lazy=True
    )
    
    assert '<picture>' in picture_tag
    assert 'image/webp' in picture_tag
    
    print("   ✓ Lazy Loading working correctly")
except Exception as e:
    print(f"   ✗ Lazy Loading test failed: {e}")
    sys.exit(1)

# Test 7: Connection Pool Optimizer
print("\n7. Testing Connection Pool Optimizer...")
try:
    optimizer = ConnectionPoolOptimizer(
        database_url='sqlite:///:memory:',
        initial_pool_size=5,
        max_overflow=10,
        pool_timeout=30
    )
    
    assert optimizer.initial_pool_size == 5
    assert optimizer.max_overflow == 10
    assert 'connections_created' in optimizer.metrics
    
    print("   ✓ Connection Pool Optimizer working correctly")
except Exception as e:
    print(f"   ✗ Connection Pool Optimizer test failed: {e}")
    sys.exit(1)

# Test 8: Pool Metrics
print("\n8. Testing Pool Metrics...")
try:
    optimizer = ConnectionPoolOptimizer(database_url='sqlite:///:memory:')
    
    optimizer.metrics['checkout_count'] = 100
    optimizer.metrics['checkin_count'] = 95
    
    stats = optimizer.get_connection_stats()
    assert stats['total_checkouts'] == 100
    assert stats['total_checkins'] == 95
    
    print("   ✓ Pool Metrics working correctly")
except Exception as e:
    print(f"   ✗ Pool Metrics test failed: {e}")
    sys.exit(1)

# Test 9: Cache Headers
print("\n9. Testing Cache Headers...")
try:
    cdn = CDNManager()
    
    # Test different file types
    jpg_headers = cdn.get_cache_headers('/static/images/logo.jpg')
    assert 'max-age=31536000' in jpg_headers['Cache-Control']
    
    css_headers = cdn.get_cache_headers('/static/css/style.css')
    assert 'max-age=604800' in css_headers['Cache-Control']
    
    html_headers = cdn.get_cache_headers('/static/index.html')
    assert 'max-age=3600' in html_headers['Cache-Control']
    
    print("   ✓ Cache Headers working correctly")
except Exception as e:
    print(f"   ✗ Cache Headers test failed: {e}")
    sys.exit(1)

# Test 10: Format Selection
print("\n10. Testing Format Selection...")
try:
    optimizer = ImageOptimizer()
    
    img = Image.new('RGB', (100, 100), color='green')
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, 'JPEG')
        temp_path = f.name
    
    try:
        chrome_ua = 'Mozilla/5.0 Chrome/91.0.4472.124'
        format_chrome = optimizer.get_optimal_format(temp_path, chrome_ua)
        assert format_chrome == 'WEBP'
        
        print("   ✓ Format Selection working correctly")
    finally:
        os.unlink(temp_path)
        
except Exception as e:
    print(f"   ✗ Format Selection test failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)
print()
print("✓ All 10 validation tests passed successfully!")
print()
print("Performance Optimization Implementation Status:")
print("  ✓ CDN Manager - Working")
print("  ✓ Asset Optimizer - Working")
print("  ✓ Image Optimizer - Working")
print("  ✓ WebP Conversion - Working")
print("  ✓ Lazy Loading - Working")
print("  ✓ Connection Pool Optimizer - Working")
print("  ✓ Pool Metrics - Working")
print("  ✓ Cache Headers - Working")
print("  ✓ Format Selection - Working")
print()
print("Phase 12: Performance Optimization is COMPLETE ✅")
print("=" * 80)
