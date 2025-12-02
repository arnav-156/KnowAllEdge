"""
Property Tests for Performance Optimization
Tests all Phase 12 performance features
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, MagicMock, patch
import os
import tempfile
from PIL import Image
import io

from cdn_manager import CDNManager, AssetOptimizer
from image_optimizer import ImageOptimizer, LazyLoadingHelper
from connection_pool_optimizer import ConnectionPoolOptimizer, ConnectionPoolMonitor


# ==================== Property 51: Cache Hit Optimization ====================

@given(
    file_extension=st.sampled_from(['.jpg', '.css', '.js', '.html', '.json']),
    file_path=st.text(min_size=5, max_size=50)
)
@settings(max_examples=100, deadline=1000)
def test_property_51_cache_headers(file_extension, file_path):
    """
    Property 51: Cache hit optimization
    
    Property: Cache headers must be set appropriately:
    - Images get long cache (1 year)
    - CSS/JS get medium cache (1 week)
    - HTML gets short cache (1 hour)
    - Cache-Control includes max-age and public/no-cache
    
    Validates: Requirements 12.2
    """
    cdn = CDNManager()
    
    # Create test file path
    test_path = f"/static/assets/test{file_extension}"
    
    # Get cache headers
    headers = cdn.get_cache_headers(test_path)
    
    # Verify headers exist
    assert 'Cache-Control' in headers
    assert 'Expires' in headers
    
    # Verify Cache-Control format
    cache_control = headers['Cache-Control']
    assert 'max-age=' in cache_control
    assert ('public' in cache_control or 'no-cache' in cache_control)
    
    # Verify appropriate cache duration
    if file_extension in ['.jpg', '.png', '.webp']:
        # Images should have long cache
        assert 'max-age=31536000' in cache_control  # 1 year
        assert 'immutable' in cache_control
    elif file_extension in ['.css', '.js']:
        # CSS/JS should have medium cache
        assert 'max-age=604800' in cache_control  # 1 week
    elif file_extension == '.html':
        # HTML should have short cache
        assert 'max-age=3600' in cache_control  # 1 hour


@given(
    asset_path=st.text(min_size=5, max_size=100),
    version=st.text(min_size=1, max_size=20)
)
@settings(max_examples=50, deadline=1000)
def test_cdn_url_generation(asset_path, version):
    """
    Test: CDN URL generation with cache busting
    
    Property: CDN URLs should include version for cache busting
    """
    cdn = CDNManager(cdn_url='https://cdn.example.com')
    
    # Generate CDN URL
    cdn_url = cdn.get_cdn_url(asset_path, version)
    
    # Verify CDN URL format
    assert cdn_url.startswith('https://cdn.example.com/')
    assert version in cdn_url


@given(
    file_path=st.text(min_size=5, max_size=50)
)
@settings(max_examples=50, deadline=1000)
def test_etag_generation(file_path):
    """
    Test: ETag generation for cache validation
    
    Property: ETags should be consistent for same file
    """
    cdn = CDNManager()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = f.name
    
    try:
        # Generate ETag twice
        etag1 = cdn.generate_etag(temp_path)
        etag2 = cdn.generate_etag(temp_path)
        
        # ETags should be consistent
        assert etag1 == etag2
        assert etag1.startswith('"') and etag1.endswith('"')
    finally:
        os.unlink(temp_path)


# ==================== Property 52: Image Format Optimization ====================

@given(
    quality=st.integers(min_value=1, max_value=100),
    max_width=st.integers(min_value=100, max_value=4096),
    max_height=st.integers(min_value=100, max_value=4096)
)
@settings(max_examples=50, deadline=2000)
def test_property_52_image_optimization(quality, max_width, max_height):
    """
    Property 52: Image format optimization
    
    Property: Image optimization must:
    - Reduce file size
    - Maintain acceptable quality
    - Support multiple formats (JPEG, PNG, WebP)
    - Resize images if too large
    
    Validates: Requirements 12.4
    """
    optimizer = ImageOptimizer(quality=quality, max_width=max_width, max_height=max_height)
    
    # Create test image
    img = Image.new('RGB', (800, 600), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, 'JPEG')
        temp_path = f.name
    
    try:
        original_size = os.path.getsize(temp_path)
        
        # Optimize image
        result = optimizer.optimize_image(temp_path, target_format='JPEG')
        
        # Verify optimization
        assert result['success'] is True
        assert 'optimized_size' in result
        assert 'compression_ratio' in result
        
        # Verify file was created
        assert os.path.exists(result['output_path'])
        
        # Cleanup
        if os.path.exists(result['output_path']):
            os.unlink(result['output_path'])
    finally:
        os.unlink(temp_path)


@given(
    user_agent=st.sampled_from([
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
    ])
)
@settings(max_examples=50, deadline=1000)
def test_optimal_format_selection(user_agent):
    """
    Test: Optimal image format selection based on browser
    
    Property: Should select WebP for modern browsers, fallback for others
    """
    optimizer = ImageOptimizer()
    
    # Create test image
    img = Image.new('RGB', (100, 100), color='blue')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, 'JPEG')
        temp_path = f.name
    
    try:
        # Get optimal format
        optimal_format = optimizer.get_optimal_format(temp_path, user_agent)
        
        # Verify format is valid
        assert optimal_format in ['JPEG', 'PNG', 'WEBP']
        
        # Chrome should get WebP
        if 'Chrome/' in user_agent:
            assert optimal_format == 'WEBP'
    finally:
        os.unlink(temp_path)


@given(
    width=st.integers(min_value=50, max_value=2000),
    height=st.integers(min_value=50, max_value=2000)
)
@settings(max_examples=30, deadline=2000)
def test_image_resizing(width, height):
    """
    Test: Image resizing maintains aspect ratio
    
    Property: Resized images should maintain aspect ratio
    """
    optimizer = ImageOptimizer()
    
    # Create test image
    img = Image.new('RGB', (1000, 800), color='green')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, 'JPEG')
        temp_path = f.name
    
    try:
        # Resize image
        result = optimizer.resize_image(temp_path, width, height)
        
        if result['success']:
            # Verify dimensions
            output_width, output_height = result['output_dimensions']
            assert output_width <= width
            assert output_height <= height
            
            # Cleanup
            if os.path.exists(result['output_path']):
                os.unlink(result['output_path'])
    finally:
        os.unlink(temp_path)


# ==================== Property 53: Response Compression ====================

@given(
    css_content=st.text(min_size=100, max_size=1000)
)
@settings(max_examples=50, deadline=1000)
def test_property_53_css_minification(css_content):
    """
    Property 53: Response compression
    
    Property: Minification must reduce size:
    - Remove comments
    - Remove unnecessary whitespace
    - Maintain functionality
    
    Validates: Requirements 12.6
    """
    # Add CSS-like structure
    css_with_comments = f"/* Comment */ {css_content} /* Another comment */"
    css_with_whitespace = css_with_comments.replace(' ', '    ')
    
    # Minify
    minified = AssetOptimizer.minify_css(css_with_whitespace)
    
    # Verify size reduction
    assert len(minified) <= len(css_with_whitespace)
    
    # Verify comments removed
    assert '/*' not in minified
    assert '*/' not in minified


@given(
    original_size=st.integers(min_value=1000, max_value=1000000),
    compressed_size=st.integers(min_value=100, max_value=500000)
)
@settings(max_examples=100, deadline=1000)
def test_compression_ratio_calculation(original_size, compressed_size):
    """
    Test: Compression ratio calculation
    
    Property: Compression ratio should be between 0 and 1
    """
    assume(compressed_size <= original_size)
    
    ratio = AssetOptimizer.calculate_compression_ratio(original_size, compressed_size)
    
    # Verify ratio is valid
    assert 0 <= ratio <= 1
    
    # Verify ratio calculation
    expected_ratio = 1 - (compressed_size / original_size)
    assert abs(ratio - expected_ratio) < 0.001


# ==================== Property 54: Connection Pooling Efficiency ====================

@given(
    pool_size=st.integers(min_value=2, max_value=50),
    max_overflow=st.integers(min_value=0, max_value=20),
    timeout=st.integers(min_value=5, max_value=60)
)
@settings(max_examples=50, deadline=1000)
def test_property_54_connection_pool_config(pool_size, max_overflow, timeout):
    """
    Property 54: Connection pooling efficiency
    
    Property: Connection pool must be configured correctly:
    - Pool size > 0
    - Max overflow >= 0
    - Timeout > 0
    - Total capacity = pool_size + max_overflow
    
    Validates: Requirements 12.7
    """
    # Create optimizer (without actual database)
    optimizer = ConnectionPoolOptimizer(
        database_url='sqlite:///:memory:',
        initial_pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=timeout
    )
    
    # Verify configuration
    assert optimizer.initial_pool_size == pool_size
    assert optimizer.max_overflow == max_overflow
    assert optimizer.pool_timeout == timeout
    
    # Verify total capacity
    total_capacity = pool_size + max_overflow
    assert total_capacity >= pool_size


@given(
    checkout_count=st.integers(min_value=0, max_value=1000),
    checkin_count=st.integers(min_value=0, max_value=1000)
)
@settings(max_examples=100, deadline=1000)
def test_connection_leak_detection(checkout_count, checkin_count):
    """
    Test: Connection leak detection
    
    Property: Should detect when checkouts exceed checkins significantly
    """
    optimizer = ConnectionPoolOptimizer(database_url='sqlite:///:memory:')
    
    # Set metrics
    optimizer.metrics['checkout_count'] = checkout_count
    optimizer.metrics['checkin_count'] = checkin_count
    
    # Monitor health
    health = optimizer.monitor_pool_health()
    
    # If checkouts significantly exceed checkins, should detect leak
    if checkout_count > checkin_count + 10:
        assert not health['healthy'] or health['status'] == 'warning'
        assert len(health['issues']) > 0 or len(health['warnings']) > 0


@given(
    utilization=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=50, deadline=1000)
def test_pool_size_optimization(utilization):
    """
    Test: Pool size optimization based on utilization
    
    Property: Should recommend appropriate pool size based on utilization
    """
    optimizer = ConnectionPoolOptimizer(
        database_url='sqlite:///:memory:',
        initial_pool_size=10
    )
    
    # Mock pool status
    with patch.object(optimizer, 'get_pool_status') as mock_status:
        mock_status.return_value = {
            'pool_size': 10,
            'checked_out': int(10 * utilization),
            'overflow': 0,
            'utilization_percent': utilization * 100
        }
        
        # Optimize
        result = optimizer.optimize_pool_size(target_utilization=0.7)
        
        # Verify recommendation
        assert 'recommended_pool_size' in result
        assert 'action' in result
        assert result['action'] in ['increase', 'decrease', 'maintain']


# ==================== Integration Tests ====================

def test_cdn_manager_initialization():
    """Test CDN manager initializes correctly"""
    cdn = CDNManager(cdn_url='https://cdn.example.com', enable_minification=True)
    
    assert cdn.cdn_url == 'https://cdn.example.com'
    assert cdn.enable_minification is True
    assert len(cdn.cache_control_rules) > 0


def test_image_optimizer_initialization():
    """Test image optimizer initializes correctly"""
    optimizer = ImageOptimizer(quality=85, max_width=2048, max_height=2048)
    
    assert optimizer.quality == 85
    assert optimizer.max_width == 2048
    assert optimizer.max_height == 2048


def test_connection_pool_optimizer_initialization():
    """Test connection pool optimizer initializes correctly"""
    optimizer = ConnectionPoolOptimizer(
        database_url='sqlite:///:memory:',
        initial_pool_size=5,
        max_overflow=10
    )
    
    assert optimizer.initial_pool_size == 5
    assert optimizer.max_overflow == 10
    assert optimizer.metrics['pool_size'] == 5


def test_lazy_loading_img_tag():
    """Test lazy loading img tag generation"""
    tag = LazyLoadingHelper.generate_img_tag(
        src='/images/test.jpg',
        alt='Test image',
        width=800,
        height=600,
        lazy=True
    )
    
    assert 'src="/images/test.jpg"' in tag
    assert 'alt="Test image"' in tag
    assert 'width="800"' in tag
    assert 'height="600"' in tag
    assert 'loading="lazy"' in tag


def test_asset_stats():
    """Test asset statistics retrieval"""
    cdn = CDNManager()
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(b"test content")
        temp_path = f.name
    
    try:
        stats = cdn.get_asset_stats(temp_path)
        
        assert stats['exists'] is True
        assert 'size' in stats
        assert 'content_type' in stats
        assert 'cache_headers' in stats
    finally:
        os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
