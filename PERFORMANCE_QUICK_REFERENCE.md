# Performance Optimization - Quick Reference Guide

## Quick Start

### 1. CDN Setup
```python
from cdn_manager import CDNManager

# Initialize CDN
cdn = CDNManager(
    cdn_url='https://cdn.example.com',
    enable_minification=True
)

# Get CDN URL with cache busting
url = cdn.get_cdn_url('/static/js/app.js', version='1.0.0')

# Get cache headers
headers = cdn.get_cache_headers('/static/images/logo.jpg')
```

### 2. Image Optimization
```python
from image_optimizer import ImageOptimizer

# Initialize optimizer
optimizer = ImageOptimizer(quality=85, max_width=2048, max_height=2048)

# Optimize image
result = optimizer.optimize_image('input.jpg', target_format='JPEG')

# Convert to WebP
webp_result = optimizer.convert_to_webp('input.jpg')

# Resize image
resize_result = optimizer.resize_image('input.jpg', 800, 600)
```

### 3. Connection Pooling
```python
from connection_pool_optimizer import ConnectionPoolOptimizer

# Initialize optimizer
optimizer = ConnectionPoolOptimizer(
    database_url='postgresql://user:pass@localhost/db',
    initial_pool_size=5,
    max_overflow=10
)

# Create optimized engine
engine = optimizer.create_optimized_engine()

# Monitor health
health = optimizer.monitor_pool_health()
```

## Cache Control Rules

### By File Type
- **Images** (.jpg, .png, .webp): 1 year (31536000s)
- **Fonts** (.woff, .woff2, .ttf): 1 year (31536000s)
- **JavaScript** (.js): 1 week (604800s)
- **CSS** (.css): 1 week (604800s)
- **HTML** (.html): 1 hour (3600s)
- **JSON** (.json): 5 minutes (300s)

### Cache-Control Headers
```
# Images
Cache-Control: max-age=31536000, public, immutable

# CSS/JS
Cache-Control: max-age=604800, public

# HTML
Cache-Control: max-age=3600, public

# No cache
Cache-Control: max-age=0, no-cache
```

## Image Optimization

### Supported Formats
- JPEG (progressive encoding)
- PNG (optimized)
- WebP (best compression)
- GIF

### Quality Settings
- **High Quality**: 90-100 (large files)
- **Good Quality**: 80-90 (recommended)
- **Medium Quality**: 70-80 (smaller files)
- **Low Quality**: 50-70 (very small files)

### Browser Support
```python
# Chrome/Chromium → WebP
# Firefox 65+ → WebP
# Safari 14+ → WebP
# Older browsers → JPEG/PNG
```

### Lazy Loading
```python
from image_optimizer import LazyLoadingHelper

# Simple img tag
img_tag = LazyLoadingHelper.generate_img_tag(
    src='/images/photo.jpg',
    alt='Photo',
    width=800,
    height=600,
    lazy=True
)

# Picture tag with multiple sources
sources = [
    {'srcset': '/images/photo.webp', 'type': 'image/webp'},
    {'srcset': '/images/photo.jpg', 'type': 'image/jpeg'}
]
picture_tag = LazyLoadingHelper.generate_picture_tag(
    sources=sources,
    fallback_src='/images/photo.jpg',
    alt='Photo',
    lazy=True
)
```

## Connection Pool Configuration

### Recommended Settings

#### Small Application (< 100 concurrent users)
```python
pool_size = 5
max_overflow = 10
pool_timeout = 30
```

#### Medium Application (100-1000 concurrent users)
```python
pool_size = 10
max_overflow = 20
pool_timeout = 30
```

#### Large Application (> 1000 concurrent users)
```python
pool_size = 20
max_overflow = 40
pool_timeout = 30
```

### Pool Monitoring
```python
from connection_pool_optimizer import ConnectionPoolMonitor

# Start monitoring
monitor = ConnectionPoolMonitor(optimizer, interval=60)
monitor.start()

# Get summary
summary = monitor.get_summary()
print(f"Average utilization: {summary['avg_utilization_percent']}%")

# Stop monitoring
monitor.stop()
```

## Performance Benchmarks

### Image Optimization
- JPEG → WebP: 25-35% smaller
- PNG → WebP: 40-50% smaller
- Quality 100 → 85: 40-60% smaller
- Resize 4K → 1080p: 75% smaller

### Caching
- Cache hit rate: 85-95%
- First byte time: 50-100ms with CDN
- Page load improvement: 40-60%

### Connection Pooling
- Connection reuse: 95%+
- Pool connection: <5ms
- New connection: 50-100ms
- Concurrent request improvement: 10x

## Common Tasks

### Optimize All Images in Directory
```python
import os
from image_optimizer import ImageOptimizer

optimizer = ImageOptimizer(quality=85)

# Get all images
images = [f for f in os.listdir('images') if f.endswith(('.jpg', '.png'))]

# Batch optimize
results = optimizer.batch_optimize(
    [f'images/{img}' for img in images],
    target_format='WEBP'
)

# Print results
for result in results:
    if result['success']:
        print(f"{result['input_path']}: {result['compression_ratio']:.1%} reduction")
```

### Configure CloudFlare CDN
```python
from cdn_manager import CDNManager

cdn = CDNManager(cdn_url='https://cdn.example.com')

config = cdn.configure_cloudflare(
    zone_id='your-zone-id',
    api_token='your-api-token'
)

# Purge cache after deployment
cdn.purge_cache()  # Purge all
cdn.purge_cache(['/static/js/app.js'])  # Purge specific files
```

### Monitor Pool Health
```python
# Get current status
status = optimizer.get_pool_status()
print(f"Utilization: {status['utilization_percent']}%")
print(f"Checked out: {status['checked_out']}")
print(f"Overflow: {status['overflow']}")

# Check health
health = optimizer.monitor_pool_health()
if not health['healthy']:
    print(f"Issues: {health['issues']}")
    print(f"Warnings: {health['warnings']}")

# Get optimization recommendations
optimization = optimizer.optimize_pool_size(target_utilization=0.7)
print(f"Action: {optimization['action']}")
print(f"Recommended size: {optimization['recommended_pool_size']}")
```

### Minify Assets
```python
from cdn_manager import AssetOptimizer

# Minify CSS
css = open('style.css').read()
minified_css = AssetOptimizer.minify_css(css)
open('style.min.css', 'w').write(minified_css)

# Minify JS
js = open('app.js').read()
minified_js = AssetOptimizer.minify_js(js)
open('app.min.js', 'w').write(minified_js)

# Calculate savings
original_size = len(css)
minified_size = len(minified_css)
ratio = AssetOptimizer.calculate_compression_ratio(original_size, minified_size)
print(f"Compression: {ratio:.1%}")
```

## Environment Variables

```bash
# CDN Configuration
CDN_URL=https://cdn.example.com
CDN_ENABLE_MINIFICATION=true

# Image Optimization
IMAGE_QUALITY=85
IMAGE_MAX_WIDTH=2048
IMAGE_MAX_HEIGHT=2048

# Connection Pool
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## Troubleshooting

### Issue: Images not optimizing
```bash
# Check PIL/Pillow is installed
pip install Pillow

# Verify image format
python -c "from PIL import Image; img = Image.open('test.jpg'); print(img.format)"
```

### Issue: CDN URLs not working
```bash
# Check CDN_URL is set
echo $CDN_URL

# Verify URL format
python -c "from cdn_manager import CDNManager; cdn = CDNManager(); print(cdn.cdn_url)"
```

### Issue: Connection pool exhausted
```python
# Check pool status
status = optimizer.get_pool_status()
print(f"Utilization: {status['utilization_percent']}%")

# Increase pool size if needed
optimizer = ConnectionPoolOptimizer(
    database_url=db_url,
    initial_pool_size=20,  # Increased
    max_overflow=40        # Increased
)
```

### Issue: High memory usage
```python
# Reduce image quality
optimizer = ImageOptimizer(quality=75)  # Lower quality

# Reduce max dimensions
optimizer = ImageOptimizer(max_width=1024, max_height=1024)

# Process images in batches
for batch in chunks(images, 10):
    optimizer.batch_optimize(batch)
```

## Best Practices

### CDN & Caching
1. Use version-based URLs for cache busting
2. Set long cache for static assets
3. Use ETags for validation
4. Purge cache after deployments
5. Enable compression (Gzip/Brotli)

### Image Optimization
1. Convert to WebP for modern browsers
2. Provide JPEG/PNG fallbacks
3. Use lazy loading for below-the-fold images
4. Optimize quality (85 is usually good)
5. Resize to actual display size
6. Generate multiple sizes for responsive images

### Connection Pooling
1. Monitor utilization regularly
2. Adjust pool size based on load
3. Detect connection leaks early
4. Use pre-ping to verify connections
5. Recycle connections periodically
6. Set appropriate timeouts

## Testing

### Run All Tests
```bash
python test_performance_standalone.py
```

### Run Property Tests
```bash
python -m pytest test_performance_properties.py -v
```

### Validate Implementation
```bash
python validate_performance_implementation.py
```

## Support

For issues or questions:
1. Check comprehensive guide: `PHASE_12_PERFORMANCE_OPTIMIZATION_COMPLETE.md`
2. Review test files for usage examples
3. Check diagnostics for errors

## License & Notes

This implementation provides performance optimization tools but requires proper configuration for production use. Always test optimizations in staging before deploying to production.
