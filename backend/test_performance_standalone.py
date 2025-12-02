"""
Standalone Performance Tests
Tests Phase 12 performance features without external dependencies
"""

import os
import sys
import tempfile
from PIL import Image

# Import performance modules
from cdn_manager import CDNManager, AssetOptimizer
from image_optimizer import ImageOptimizer, LazyLoadingHelper
from connection_pool_optimizer import ConnectionPoolOptimizer


def test_cdn_manager():
    """Test CDN manager functionality"""
    print("Testing CDN Manager...")
    
    cdn = CDNManager(cdn_url='https://cdn.example.com', enable_minification=True)
    
    # Test CDN URL generation
    url = cdn.get_cdn_url('/static/js/app.js', version='1.0.0')
    assert 'cdn.example.com' in url, "CDN URL not generated correctly"
    assert 'v=1.0.0' in url, "Version not included in URL"
    
    # Test cache headers
    headers = cdn.get_cache_headers('/static/images/logo.jpg')
    assert 'Cache-Control' in headers, "Cache-Control header missing"
    assert 'max-age=31536000' in headers['Cache-Control'], "Image cache duration incorrect"
    
    # Test minification check
    assert cdn.should_minify('/static/js/app.js') is True, "JS should be minified"
    assert cdn.should_minify('/static/js/app.min.js') is False, "Already minified JS should not be minified again"
    
    print("   ✓ CDN Manager test passed")


def test_asset_optimizer():
    """Test asset optimization"""
    print("Testing Asset Optimizer...")
    
    # Test CSS minification
    css = """
    /* This is a comment */
    body {
        margin: 0;
        padding: 0;
    }
    /* Another comment */
    """
    
    minified = AssetOptimizer.minify_css(css)
    assert len(minified) < len(css), "CSS not minified"
    assert '/*' not in minified, "Comments not removed"
    
    # Test compression ratio
    ratio = AssetOptimizer.calculate_compression_ratio(1000, 500)
    assert ratio == 0.5, "Compression ratio calculation incorrect"
    
    print("   ✓ Asset Optimizer test passed")


def test_image_optimizer():
    """Test image optimization"""
    print("Testing Image Optimizer...")
    
    optimizer = ImageOptimizer(quality=85, max_width=1024, max_height=1024)
    
    # Create test image
    img = Image.new('RGB', (800, 600), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, 'JPEG', quality=100)
        temp_path = f.name
    
    try:
        original_size = os.path.getsize(temp_path)
        
        # Optimize image
        result = optimizer.optimize_image(temp_path, target_format='JPEG')
        
        assert result['success'] is True, "Image optimization failed"
        assert result['optimized_size'] <= original_size, "Optimized image not smaller"
        assert os.path.exists(result['output_path']), "Output file not created"
        
        # Test WebP conversion
        webp_result = optimizer.convert_to_webp(temp_path)
        assert webp_result['success'] is True, "WebP conversion failed"
        assert webp_result['output_format'] == 'WEBP', "Format not WebP"
        
        # Cleanup
        if os.path.exists(result['output_path']):
            os.unlink(result['output_path'])
        if os.path.exists(webp_result['output_path']):
            os.unlink(webp_result['output_path'])
        
        print("   ✓ Image Optimizer test passed")
        
    finally:
        os.unlink(temp_path)


def test_image_resizing():
    """Test image resizing"""
    print("Testing Image Resizing...")
    
    optimizer = ImageOptimizer()
    
    # Create test image
    img = Image.new('RGB', (1000, 800), color='blue')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, 'JPEG')
        temp_path = f.name
    
    try:
        # Resize image
        result = optimizer.resize_image(temp_path, 500, 400)
        
        assert result['success'] is True, "Image resize failed"
        assert result['output_dimensions'][0] <= 500, "Width not resized correctly"
        assert result['output_dimensions'][1] <= 400, "Height not resized correctly"
        
        # Cleanup
        if os.path.exists(result['output_path']):
            os.unlink(result['output_path'])
        
        print("   ✓ Image Resizing test passed")
        
    finally:
        os.unlink(temp_path)


def test_optimal_format_selection():
    """Test optimal format selection"""
    print("Testing Optimal Format Selection...")
    
    optimizer = ImageOptimizer()
    
    # Create test image
    img = Image.new('RGB', (100, 100), color='green')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, 'JPEG')
        temp_path = f.name
    
    try:
        # Test Chrome (should get WebP)
        chrome_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        format_chrome = optimizer.get_optimal_format(temp_path, chrome_ua)
        assert format_chrome == 'WEBP', "Chrome should get WebP"
        
        # Test old browser (should get JPEG)
        old_ua = 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'
        format_old = optimizer.get_optimal_format(temp_path, old_ua)
        assert format_old in ['JPEG', 'PNG'], "Old browser should get JPEG or PNG"
        
        print("   ✓ Optimal Format Selection test passed")
        
    finally:
        os.unlink(temp_path)


def test_lazy_loading():
    """Test lazy loading HTML generation"""
    print("Testing Lazy Loading...")
    
    # Test img tag
    img_tag = LazyLoadingHelper.generate_img_tag(
        src='/images/test.jpg',
        alt='Test image',
        width=800,
        height=600,
        lazy=True
    )
    
    assert 'src="/images/test.jpg"' in img_tag, "Source not in tag"
    assert 'alt="Test image"' in img_tag, "Alt text not in tag"
    assert 'loading="lazy"' in img_tag, "Lazy loading not enabled"
    
    # Test picture tag
    sources = [
        {'srcset': '/images/test.webp', 'type': 'image/webp'},
        {'srcset': '/images/test.jpg', 'type': 'image/jpeg'}
    ]
    picture_tag = LazyLoadingHelper.generate_picture_tag(
        sources=sources,
        fallback_src='/images/test.jpg',
        alt='Test image',
        lazy=True
    )
    
    assert '<picture>' in picture_tag, "Picture tag not generated"
    assert 'image/webp' in picture_tag, "WebP source not included"
    assert 'loading="lazy"' in picture_tag, "Lazy loading not enabled"
    
    print("   ✓ Lazy Loading test passed")


def test_connection_pool_optimizer():
    """Test connection pool optimizer"""
    print("Testing Connection Pool Optimizer...")
    
    optimizer = ConnectionPoolOptimizer(
        database_url='sqlite:///:memory:',
        initial_pool_size=5,
        max_overflow=10,
        pool_timeout=30
    )
    
    # Test configuration
    assert optimizer.initial_pool_size == 5, "Pool size not set correctly"
    assert optimizer.max_overflow == 10, "Max overflow not set correctly"
    assert optimizer.pool_timeout == 30, "Timeout not set correctly"
    
    # Test metrics initialization
    assert 'connections_created' in optimizer.metrics, "Metrics not initialized"
    assert optimizer.metrics['pool_size'] == 5, "Initial pool size incorrect"
    
    # Test health monitoring (without actual engine)
    # Health check requires engine, so just verify metrics exist
    assert 'connections_created' in optimizer.metrics
    assert 'checkout_count' in optimizer.metrics
    
    print("   ✓ Connection Pool Optimizer test passed")


def test_pool_optimization():
    """Test pool size optimization"""
    print("Testing Pool Size Optimization...")
    
    optimizer = ConnectionPoolOptimizer(
        database_url='sqlite:///:memory:',
        initial_pool_size=10
    )
    
    # Simulate high utilization
    optimizer.metrics['checkout_count'] = 100
    optimizer.metrics['checkin_count'] = 90
    
    # Test connection stats
    stats = optimizer.get_connection_stats()
    assert 'total_checkouts' in stats, "Stats missing checkouts"
    assert stats['total_checkouts'] == 100, "Checkout count incorrect"
    
    print("   ✓ Pool Size Optimization test passed")


def test_cache_headers():
    """Test cache header generation"""
    print("Testing Cache Headers...")
    
    cdn = CDNManager()
    
    # Test different file types
    test_files = {
        '/static/images/logo.jpg': 31536000,  # 1 year
        '/static/css/style.css': 604800,      # 1 week
        '/static/js/app.js': 604800,          # 1 week
        '/static/index.html': 3600,           # 1 hour
        '/api/data.json': 300                 # 5 minutes
    }
    
    for file_path, expected_max_age in test_files.items():
        headers = cdn.get_cache_headers(file_path)
        assert f'max-age={expected_max_age}' in headers['Cache-Control'], \
            f"Cache duration incorrect for {file_path}"
    
    print("   ✓ Cache Headers test passed")


def test_etag_generation():
    """Test ETag generation"""
    print("Testing ETag Generation...")
    
    cdn = CDNManager()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = f.name
    
    try:
        # Generate ETag
        etag = cdn.generate_etag(temp_path)
        
        assert etag.startswith('"') and etag.endswith('"'), "ETag format incorrect"
        
        # ETag should be consistent
        etag2 = cdn.generate_etag(temp_path)
        assert etag == etag2, "ETag not consistent"
        
        print("   ✓ ETag Generation test passed")
        
    finally:
        os.unlink(temp_path)


def run_all_tests():
    """Run all performance tests"""
    print("\n" + "=" * 80)
    print("Performance Optimization Tests (Phase 12)")
    print("=" * 80 + "\n")
    
    tests = [
        test_cdn_manager,
        test_asset_optimizer,
        test_image_optimizer,
        test_image_resizing,
        test_optimal_format_selection,
        test_lazy_loading,
        test_connection_pool_optimizer,
        test_pool_optimization,
        test_cache_headers,
        test_etag_generation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
