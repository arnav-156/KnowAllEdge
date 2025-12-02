"""
CDN Manager for Static Assets
Manages CDN configuration and asset delivery optimization
"""

import os
import hashlib
import mimetypes
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CDNManager:
    """
    CDN Manager for static asset delivery
    Handles CDN configuration, caching headers, and asset optimization
    """
    
    def __init__(self, cdn_url: Optional[str] = None, enable_minification: bool = True):
        """
        Initialize CDN Manager
        
        Args:
            cdn_url: CDN base URL (e.g., 'https://cdn.example.com')
            enable_minification: Whether to enable automatic minification
        """
        self.cdn_url = cdn_url or os.getenv('CDN_URL', '')
        self.enable_minification = enable_minification
        self.cache_control_rules = self._default_cache_rules()
    
    def _default_cache_rules(self) -> Dict[str, Dict[str, any]]:
        """
        Default cache control rules for different asset types
        
        Returns:
            Dictionary of cache rules by file extension
        """
        return {
            # Images - long cache (1 year)
            '.jpg': {'max_age': 31536000, 'immutable': True},
            '.jpeg': {'max_age': 31536000, 'immutable': True},
            '.png': {'max_age': 31536000, 'immutable': True},
            '.gif': {'max_age': 31536000, 'immutable': True},
            '.webp': {'max_age': 31536000, 'immutable': True},
            '.svg': {'max_age': 31536000, 'immutable': True},
            '.ico': {'max_age': 31536000, 'immutable': True},
            
            # Fonts - long cache (1 year)
            '.woff': {'max_age': 31536000, 'immutable': True},
            '.woff2': {'max_age': 31536000, 'immutable': True},
            '.ttf': {'max_age': 31536000, 'immutable': True},
            '.eot': {'max_age': 31536000, 'immutable': True},
            
            # JavaScript - medium cache (1 week)
            '.js': {'max_age': 604800, 'immutable': False},
            '.mjs': {'max_age': 604800, 'immutable': False},
            
            # CSS - medium cache (1 week)
            '.css': {'max_age': 604800, 'immutable': False},
            
            # HTML - short cache (1 hour)
            '.html': {'max_age': 3600, 'immutable': False},
            
            # JSON - short cache (5 minutes)
            '.json': {'max_age': 300, 'immutable': False},
            
            # Default - no cache
            'default': {'max_age': 0, 'immutable': False}
        }
    
    def get_cdn_url(self, asset_path: str, version: Optional[str] = None) -> str:
        """
        Get CDN URL for an asset
        
        Args:
            asset_path: Path to asset (e.g., '/static/js/app.js')
            version: Optional version/hash for cache busting
            
        Returns:
            Full CDN URL or original path if CDN not configured
        """
        if not self.cdn_url:
            return asset_path
        
        # Remove leading slash
        asset_path = asset_path.lstrip('/')
        
        # Add version for cache busting
        if version:
            separator = '&' if '?' in asset_path else '?'
            asset_path = f"{asset_path}{separator}v={version}"
        
        return f"{self.cdn_url}/{asset_path}"
    
    def get_cache_headers(self, file_path: str) -> Dict[str, str]:
        """
        Get cache control headers for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary of cache headers
        """
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Get cache rule
        rule = self.cache_control_rules.get(ext, self.cache_control_rules['default'])
        
        # Build Cache-Control header
        cache_control_parts = [f"max-age={rule['max_age']}"]
        
        if rule['max_age'] > 0:
            cache_control_parts.append('public')
        else:
            cache_control_parts.append('no-cache')
        
        if rule['immutable']:
            cache_control_parts.append('immutable')
        
        cache_control = ', '.join(cache_control_parts)
        
        # Calculate Expires header
        expires = datetime.utcnow() + timedelta(seconds=rule['max_age'])
        expires_str = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        headers = {
            'Cache-Control': cache_control,
            'Expires': expires_str
        }
        
        # Add ETag if file exists
        if os.path.exists(file_path):
            etag = self.generate_etag(file_path)
            headers['ETag'] = etag
        
        return headers
    
    def generate_etag(self, file_path: str) -> str:
        """
        Generate ETag for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            ETag value
        """
        try:
            # Use file modification time and size for ETag
            stat = os.stat(file_path)
            mtime = int(stat.st_mtime)
            size = stat.st_size
            
            # Create hash
            etag_data = f"{mtime}-{size}"
            etag_hash = hashlib.md5(etag_data.encode()).hexdigest()
            
            return f'"{etag_hash}"'
        except Exception as e:
            logger.error(f"Failed to generate ETag for {file_path}: {e}")
            return '"default-etag"'
    
    def should_minify(self, file_path: str) -> bool:
        """
        Check if file should be minified
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file should be minified
        """
        if not self.enable_minification:
            return False
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Minify JS, CSS, HTML
        minifiable_extensions = ['.js', '.css', '.html', '.svg']
        
        # Don't minify if already minified
        if '.min.' in file_path:
            return False
        
        return ext in minifiable_extensions
    
    def get_content_type(self, file_path: str) -> str:
        """
        Get content type for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Content-Type header value
        """
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or 'application/octet-stream'
    
    def configure_cloudflare(self, zone_id: str, api_token: str) -> Dict[str, any]:
        """
        Configure CloudFlare CDN settings
        
        Args:
            zone_id: CloudFlare zone ID
            api_token: CloudFlare API token
            
        Returns:
            Configuration result
        """
        # This would integrate with CloudFlare API
        # For now, return configuration template
        config = {
            'zone_id': zone_id,
            'settings': {
                'minify': {
                    'css': True,
                    'html': True,
                    'js': True
                },
                'browser_cache_ttl': 31536000,  # 1 year
                'cache_level': 'aggressive',
                'always_online': True,
                'development_mode': False,
                'brotli': True
            }
        }
        
        logger.info(f"CloudFlare configuration prepared for zone {zone_id}")
        return config
    
    def purge_cache(self, paths: Optional[List[str]] = None) -> bool:
        """
        Purge CDN cache for specific paths or all
        
        Args:
            paths: List of paths to purge (None = purge all)
            
        Returns:
            True if successful
        """
        if paths:
            logger.info(f"Purging CDN cache for {len(paths)} paths")
        else:
            logger.info("Purging entire CDN cache")
        
        # This would integrate with CDN API
        # For now, just log the action
        return True
    
    def get_asset_stats(self, file_path: str) -> Dict[str, any]:
        """
        Get statistics for an asset
        
        Args:
            file_path: Path to file
            
        Returns:
            Asset statistics
        """
        if not os.path.exists(file_path):
            return {'exists': False}
        
        stat = os.stat(file_path)
        
        return {
            'exists': True,
            'size': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'content_type': self.get_content_type(file_path),
            'should_minify': self.should_minify(file_path),
            'cache_headers': self.get_cache_headers(file_path)
        }


class AssetOptimizer:
    """
    Asset optimization utilities
    Handles minification, compression, and optimization
    """
    
    @staticmethod
    def minify_css(css_content: str) -> str:
        """
        Minify CSS content
        
        Args:
            css_content: CSS content
            
        Returns:
            Minified CSS
        """
        # Remove comments
        import re
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r'\s*([{}:;,])\s*', r'\1', css_content)
        
        return css_content.strip()
    
    @staticmethod
    def minify_js(js_content: str) -> str:
        """
        Minify JavaScript content (basic)
        
        Args:
            js_content: JavaScript content
            
        Returns:
            Minified JavaScript
        """
        # Remove single-line comments
        import re
        js_content = re.sub(r'//.*?$', '', js_content, flags=re.MULTILINE)
        
        # Remove multi-line comments
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # Remove extra whitespace
        js_content = re.sub(r'\s+', ' ', js_content)
        
        return js_content.strip()
    
    @staticmethod
    def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
        """
        Calculate compression ratio
        
        Args:
            original_size: Original file size
            compressed_size: Compressed file size
            
        Returns:
            Compression ratio (0-1)
        """
        if original_size == 0:
            return 0.0
        
        return 1 - (compressed_size / original_size)
