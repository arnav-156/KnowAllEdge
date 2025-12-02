"""
Image Optimization Service
Handles image conversion, resizing, and format optimization
"""

import os
import io
from typing import Optional, Tuple, Dict, List
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """
    Image optimization service
    Handles WebP conversion, resizing, and format selection
    """
    
    def __init__(self, quality: int = 85, max_width: int = 2048, max_height: int = 2048):
        """
        Initialize image optimizer
        
        Args:
            quality: JPEG/WebP quality (1-100)
            max_width: Maximum image width
            max_height: Maximum image height
        """
        self.quality = quality
        self.max_width = max_width
        self.max_height = max_height
        self.supported_formats = ['JPEG', 'PNG', 'GIF', 'WEBP']
    
    def optimize_image(self, image_path: str, output_path: Optional[str] = None,
                      target_format: Optional[str] = None) -> Dict[str, any]:
        """
        Optimize an image
        
        Args:
            image_path: Path to input image
            output_path: Path to output image (optional)
            target_format: Target format (JPEG, PNG, WEBP)
            
        Returns:
            Optimization result with statistics
        """
        try:
            # Open image
            with Image.open(image_path) as img:
                original_size = os.path.getsize(image_path)
                original_format = img.format
                original_dimensions = img.size
                
                # Convert RGBA to RGB if saving as JPEG
                if target_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Resize if needed
                if img.width > self.max_width or img.height > self.max_height:
                    img = self._resize_image(img, self.max_width, self.max_height)
                
                # Determine output path
                if not output_path:
                    base, _ = os.path.splitext(image_path)
                    ext = self._get_extension(target_format or original_format)
                    output_path = f"{base}_optimized{ext}"
                
                # Save optimized image
                save_kwargs = self._get_save_kwargs(target_format or original_format)
                img.save(output_path, **save_kwargs)
                
                # Get statistics
                optimized_size = os.path.getsize(output_path)
                compression_ratio = 1 - (optimized_size / original_size)
                
                result = {
                    'success': True,
                    'input_path': image_path,
                    'output_path': output_path,
                    'original_format': original_format,
                    'output_format': target_format or original_format,
                    'original_size': original_size,
                    'optimized_size': optimized_size,
                    'size_reduction': original_size - optimized_size,
                    'compression_ratio': compression_ratio,
                    'original_dimensions': original_dimensions,
                    'output_dimensions': img.size
                }
                
                logger.info(f"Optimized {image_path}: {compression_ratio:.1%} reduction")
                return result
                
        except Exception as e:
            logger.error(f"Failed to optimize image {image_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_path': image_path
            }
    
    def convert_to_webp(self, image_path: str, output_path: Optional[str] = None) -> Dict[str, any]:
        """
        Convert image to WebP format
        
        Args:
            image_path: Path to input image
            output_path: Path to output WebP image
            
        Returns:
            Conversion result
        """
        if not output_path:
            base, _ = os.path.splitext(image_path)
            output_path = f"{base}.webp"
        
        return self.optimize_image(image_path, output_path, 'WEBP')
    
    def resize_image(self, image_path: str, width: int, height: int,
                    output_path: Optional[str] = None) -> Dict[str, any]:
        """
        Resize an image
        
        Args:
            image_path: Path to input image
            width: Target width
            height: Target height
            output_path: Path to output image
            
        Returns:
            Resize result
        """
        try:
            with Image.open(image_path) as img:
                original_size = img.size
                
                # Resize
                resized = self._resize_image(img, width, height)
                
                # Determine output path
                if not output_path:
                    base, ext = os.path.splitext(image_path)
                    output_path = f"{base}_{width}x{height}{ext}"
                
                # Save
                save_kwargs = self._get_save_kwargs(img.format)
                resized.save(output_path, **save_kwargs)
                
                return {
                    'success': True,
                    'input_path': image_path,
                    'output_path': output_path,
                    'original_dimensions': original_size,
                    'output_dimensions': resized.size
                }
                
        except Exception as e:
            logger.error(f"Failed to resize image {image_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_path': image_path
            }
    
    def create_thumbnail(self, image_path: str, size: Tuple[int, int] = (150, 150),
                        output_path: Optional[str] = None) -> Dict[str, any]:
        """
        Create thumbnail from image
        
        Args:
            image_path: Path to input image
            size: Thumbnail size (width, height)
            output_path: Path to output thumbnail
            
        Returns:
            Thumbnail creation result
        """
        try:
            with Image.open(image_path) as img:
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Determine output path
                if not output_path:
                    base, ext = os.path.splitext(image_path)
                    output_path = f"{base}_thumb{ext}"
                
                # Save
                save_kwargs = self._get_save_kwargs(img.format)
                img.save(output_path, **save_kwargs)
                
                return {
                    'success': True,
                    'input_path': image_path,
                    'output_path': output_path,
                    'thumbnail_size': img.size
                }
                
        except Exception as e:
            logger.error(f"Failed to create thumbnail for {image_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'input_path': image_path
            }
    
    def get_optimal_format(self, image_path: str, user_agent: Optional[str] = None) -> str:
        """
        Determine optimal image format based on browser support
        
        Args:
            image_path: Path to image
            user_agent: Browser user agent string
            
        Returns:
            Optimal format (WEBP, JPEG, PNG)
        """
        # Check WebP support
        if user_agent and self._supports_webp(user_agent):
            return 'WEBP'
        
        # Check if image has transparency
        try:
            with Image.open(image_path) as img:
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    return 'PNG'
                else:
                    return 'JPEG'
        except Exception:
            return 'JPEG'
    
    def batch_optimize(self, image_paths: List[str], target_format: Optional[str] = None) -> List[Dict[str, any]]:
        """
        Optimize multiple images
        
        Args:
            image_paths: List of image paths
            target_format: Target format for all images
            
        Returns:
            List of optimization results
        """
        results = []
        
        for image_path in image_paths:
            result = self.optimize_image(image_path, target_format=target_format)
            results.append(result)
        
        # Calculate summary statistics
        successful = [r for r in results if r.get('success')]
        total_original = sum(r.get('original_size', 0) for r in successful)
        total_optimized = sum(r.get('optimized_size', 0) for r in successful)
        
        logger.info(f"Batch optimization complete: {len(successful)}/{len(image_paths)} successful")
        logger.info(f"Total size reduction: {total_original - total_optimized} bytes")
        
        return results
    
    def _resize_image(self, img: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """
        Resize image maintaining aspect ratio
        
        Args:
            img: PIL Image
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Resized image
        """
        # Calculate new dimensions
        width, height = img.size
        aspect_ratio = width / height
        
        if width > max_width:
            width = max_width
            height = int(width / aspect_ratio)
        
        if height > max_height:
            height = max_height
            width = int(height * aspect_ratio)
        
        # Resize
        return img.resize((width, height), Image.Resampling.LANCZOS)
    
    def _get_save_kwargs(self, format: str) -> Dict[str, any]:
        """
        Get save parameters for image format
        
        Args:
            format: Image format
            
        Returns:
            Save parameters
        """
        if format == 'JPEG':
            return {
                'format': 'JPEG',
                'quality': self.quality,
                'optimize': True,
                'progressive': True
            }
        elif format == 'WEBP':
            return {
                'format': 'WEBP',
                'quality': self.quality,
                'method': 6  # Best compression
            }
        elif format == 'PNG':
            return {
                'format': 'PNG',
                'optimize': True
            }
        else:
            return {'format': format}
    
    def _get_extension(self, format: str) -> str:
        """
        Get file extension for format
        
        Args:
            format: Image format
            
        Returns:
            File extension
        """
        extensions = {
            'JPEG': '.jpg',
            'PNG': '.png',
            'GIF': '.gif',
            'WEBP': '.webp'
        }
        return extensions.get(format, '.jpg')
    
    def _supports_webp(self, user_agent: str) -> bool:
        """
        Check if browser supports WebP
        
        Args:
            user_agent: Browser user agent string
            
        Returns:
            True if WebP is supported
        """
        # Modern browsers that support WebP
        webp_browsers = [
            'Chrome/', 'Chromium/', 'Edge/', 'Opera/',
            'Firefox/65', 'Firefox/66', 'Firefox/67',  # Firefox 65+
            'Safari/14', 'Safari/15', 'Safari/16'  # Safari 14+
        ]
        
        return any(browser in user_agent for browser in webp_browsers)
    
    def get_image_info(self, image_path: str) -> Dict[str, any]:
        """
        Get information about an image
        
        Args:
            image_path: Path to image
            
        Returns:
            Image information
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'path': image_path,
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'file_size': os.path.getsize(image_path),
                    'has_transparency': img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
                }
        except Exception as e:
            return {
                'path': image_path,
                'error': str(e)
            }


# Lazy loading HTML generator
class LazyLoadingHelper:
    """
    Helper for generating lazy loading HTML
    """
    
    @staticmethod
    def generate_img_tag(src: str, alt: str = '', width: Optional[int] = None,
                        height: Optional[int] = None, lazy: bool = True) -> str:
        """
        Generate img tag with lazy loading
        
        Args:
            src: Image source URL
            alt: Alt text
            width: Image width
            height: Image height
            lazy: Enable lazy loading
            
        Returns:
            HTML img tag
        """
        attrs = [f'src="{src}"', f'alt="{alt}"']
        
        if width:
            attrs.append(f'width="{width}"')
        if height:
            attrs.append(f'height="{height}"')
        if lazy:
            attrs.append('loading="lazy"')
        
        return f'<img {" ".join(attrs)} />'
    
    @staticmethod
    def generate_picture_tag(sources: List[Dict[str, str]], fallback_src: str,
                           alt: str = '', lazy: bool = True) -> str:
        """
        Generate picture tag with multiple sources
        
        Args:
            sources: List of source dictionaries with 'srcset' and 'type'
            fallback_src: Fallback image source
            alt: Alt text
            lazy: Enable lazy loading
            
        Returns:
            HTML picture tag
        """
        source_tags = []
        for source in sources:
            srcset = source.get('srcset', '')
            media_type = source.get('type', '')
            source_tags.append(f'<source srcset="{srcset}" type="{media_type}" />')
        
        img_attrs = [f'src="{fallback_src}"', f'alt="{alt}"']
        if lazy:
            img_attrs.append('loading="lazy"')
        
        img_tag = f'<img {" ".join(img_attrs)} />'
        
        return f'<picture>\n  {chr(10).join(source_tags)}\n  {img_tag}\n</picture>'
