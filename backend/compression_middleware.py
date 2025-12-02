"""
Response Compression Middleware
Implements Brotli and gzip compression for HTTP responses
Requirements: 12.8 - Enable response compression
"""

import gzip
import io
from flask import request, Response
from functools import wraps

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    print("⚠️  Brotli not available, install with: pip install brotli")


class CompressionMiddleware:
    """Middleware for compressing HTTP responses"""
    
    def __init__(self, app=None, compression_level=6, min_size=500):
        """
        Initialize compression middleware
        
        Args:
            app: Flask application
            compression_level: Compression level (1-9 for gzip, 0-11 for brotli)
            min_size: Minimum response size in bytes to compress
        """
        self.compression_level = compression_level
        self.min_size = min_size
        self.compressible_types = {
            'text/html',
            'text/css',
            'text/plain',
            'text/xml',
            'text/javascript',
            'application/json',
            'application/javascript',
            'application/xml',
            'application/xhtml+xml',
            'application/rss+xml',
            'application/atom+xml',
            'image/svg+xml'
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        app.after_request(self.compress_response)
        print(f"✅ Compression middleware initialized (level: {self.compression_level})")
    
    def should_compress(self, response):
        """Check if response should be compressed"""
        # Don't compress if already compressed
        if response.headers.get('Content-Encoding'):
            return False
        
        # Don't compress small responses
        if response.content_length and response.content_length < self.min_size:
            return False
        
        # Check content type
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
        if content_type not in self.compressible_types:
            return False
        
        # Don't compress if client doesn't support it
        accept_encoding = request.headers.get('Accept-Encoding', '').lower()
        if not accept_encoding:
            return False
        
        return True
    
    def compress_response(self, response):
        """Compress response if appropriate"""
        if not self.should_compress(response):
            return response
        
        accept_encoding = request.headers.get('Accept-Encoding', '').lower()
        
        # Try Brotli first (better compression)
        if BROTLI_AVAILABLE and 'br' in accept_encoding:
            return self._compress_brotli(response)
        
        # Fall back to gzip
        if 'gzip' in accept_encoding:
            return self._compress_gzip(response)
        
        return response
    
    def _compress_brotli(self, response):
        """Compress response with Brotli"""
        try:
            # Get response data
            data = response.get_data()
            
            # Compress with Brotli
            compressed_data = brotli.compress(
                data,
                quality=self.compression_level
            )
            
            # Calculate compression ratio
            original_size = len(data)
            compressed_size = len(compressed_data)
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            # Create new response
            response.set_data(compressed_data)
            response.headers['Content-Encoding'] = 'br'
            response.headers['Content-Length'] = len(compressed_data)
            response.headers['X-Compression-Ratio'] = f'{ratio:.1f}%'
            response.headers['Vary'] = 'Accept-Encoding'
            
            return response
            
        except Exception as e:
            print(f"Brotli compression error: {e}")
            return response
    
    def _compress_gzip(self, response):
        """Compress response with gzip"""
        try:
            # Get response data
            data = response.get_data()
            
            # Compress with gzip
            gzip_buffer = io.BytesIO()
            with gzip.GzipFile(
                mode='wb',
                compresslevel=self.compression_level,
                fileobj=gzip_buffer
            ) as gzip_file:
                gzip_file.write(data)
            
            compressed_data = gzip_buffer.getvalue()
            
            # Calculate compression ratio
            original_size = len(data)
            compressed_size = len(compressed_data)
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            # Create new response
            response.set_data(compressed_data)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(compressed_data)
            response.headers['X-Compression-Ratio'] = f'{ratio:.1f}%'
            response.headers['Vary'] = 'Accept-Encoding'
            
            return response
            
        except Exception as e:
            print(f"Gzip compression error: {e}")
            return response


def compress_response(compression_level=6):
    """Decorator to compress individual route responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            
            # Convert to Response object if needed
            if not isinstance(response, Response):
                response = Response(response)
            
            # Apply compression
            middleware = CompressionMiddleware(compression_level=compression_level)
            return middleware.compress_response(response)
        
        return wrapper
    return decorator


class StaticFileCompression:
    """Pre-compress static files for serving"""
    
    def __init__(self, static_folder):
        self.static_folder = static_folder
        self.compressed_files = {}
    
    def precompress_files(self):
        """Pre-compress static files"""
        import os
        
        print("Pre-compressing static files...")
        
        for root, dirs, files in os.walk(self.static_folder):
            for file in files:
                if self._should_precompress(file):
                    file_path = os.path.join(root, file)
                    self._compress_file(file_path)
        
        print(f"✅ Pre-compressed {len(self.compressed_files)} files")
    
    def _should_precompress(self, filename):
        """Check if file should be pre-compressed"""
        compressible_extensions = {
            '.js', '.css', '.html', '.xml', '.json',
            '.svg', '.txt', '.md'
        }
        return any(filename.endswith(ext) for ext in compressible_extensions)
    
    def _compress_file(self, file_path):
        """Compress a single file"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Create gzip version
            gzip_path = f"{file_path}.gz"
            with gzip.open(gzip_path, 'wb', compresslevel=9) as f:
                f.write(data)
            
            # Create brotli version if available
            if BROTLI_AVAILABLE:
                br_path = f"{file_path}.br"
                with open(br_path, 'wb') as f:
                    f.write(brotli.compress(data, quality=11))
            
            self.compressed_files[file_path] = True
            
        except Exception as e:
            print(f"Error compressing {file_path}: {e}")


def get_compression_stats(app):
    """Get compression statistics"""
    stats = {
        'brotli_available': BROTLI_AVAILABLE,
        'compression_enabled': True,
        'compressible_types': len(CompressionMiddleware().compressible_types)
    }
    
    return stats


def setup_compression(app, compression_level=6, min_size=500):
    """Setup compression for Flask app"""
    middleware = CompressionMiddleware(
        app=app,
        compression_level=compression_level,
        min_size=min_size
    )
    
    # Add compression info endpoint
    @app.route('/api/compression/info')
    def compression_info():
        return {
            'brotli_available': BROTLI_AVAILABLE,
            'compression_level': compression_level,
            'min_size': min_size,
            'status': 'enabled'
        }
    
    return middleware


# Example usage in Flask app:
"""
from compression_middleware import setup_compression

app = Flask(__name__)
setup_compression(app, compression_level=6, min_size=500)
"""
