"""
File Upload Validation Module

Secure file upload validation with extension and size checks
"""

import os
from typing import Tuple, Optional
from dataclasses import dataclass
from werkzeug.utils import secure_filename
from structured_logging import get_logger

# Try to import python-magic, but make it optional
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger = get_logger(__name__)
    logger.warning("python-magic not available, MIME type detection will be skipped")

logger = get_logger(__name__)


@dataclass
class FileValidationResult:
    """Result of file validation"""
    is_valid: bool
    errors: list
    safe_filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class FileValidator:
    """
    Validates uploaded files for security
    
    Checks:
    - File extension whitelist
    - File size limits
    - MIME type validation
    - Malicious content scanning
    """
    
    # Maximum file size (10 MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'doc', 'docx', 'md', 'json', 'csv',
        'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'
    }
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'text/plain',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/markdown',
        'application/json',
        'text/csv',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/svg+xml'
    }
    
    # Dangerous file patterns
    DANGEROUS_PATTERNS = [
        b'<script',
        b'javascript:',
        b'<?php',
        b'<%',
        b'#!/bin/bash',
        b'#!/bin/sh'
    ]
    
    def __init__(self):
        logger.info("FileValidator initialized")
    
    def validate_file(self, file_obj, filename: str) -> FileValidationResult:
        """
        Validate uploaded file
        
        Args:
            file_obj: File object from request.files
            filename: Original filename
        
        Returns:
            FileValidationResult with validation status
        """
        errors = []
        
        # Validate filename
        if not filename:
            errors.append("Filename is required")
            return FileValidationResult(is_valid=False, errors=errors)
        
        # Secure the filename
        safe_filename = secure_filename(filename)
        
        if not safe_filename:
            errors.append("Invalid filename")
            return FileValidationResult(is_valid=False, errors=errors)
        
        # Validate extension
        extension = self._get_extension(safe_filename)
        
        if not extension:
            errors.append("File must have an extension")
            return FileValidationResult(is_valid=False, errors=errors)
        
        if extension not in self.ALLOWED_EXTENSIONS:
            errors.append(f"File extension '.{extension}' is not allowed")
            logger.warning(f"Rejected file with extension: {extension}")
            return FileValidationResult(is_valid=False, errors=errors)
        
        # Read file content
        try:
            file_content = file_obj.read()
            file_size = len(file_content)
            
            # Reset file pointer
            file_obj.seek(0)
            
        except Exception as e:
            errors.append(f"Failed to read file: {str(e)}")
            logger.error(f"File read error: {e}")
            return FileValidationResult(is_valid=False, errors=errors)
        
        # Validate file size
        if file_size > self.MAX_FILE_SIZE:
            errors.append(f"File size ({file_size} bytes) exceeds maximum ({self.MAX_FILE_SIZE} bytes)")
            logger.warning(f"File too large: {file_size} bytes")
            return FileValidationResult(is_valid=False, errors=errors)
        
        if file_size == 0:
            errors.append("File is empty")
            return FileValidationResult(is_valid=False, errors=errors)
        
        # Validate MIME type (if python-magic is available)
        mime_type = None
        if MAGIC_AVAILABLE:
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
                
                if mime_type not in self.ALLOWED_MIME_TYPES:
                    errors.append(f"File type '{mime_type}' is not allowed")
                    logger.warning(f"Rejected file with MIME type: {mime_type}")
                    return FileValidationResult(is_valid=False, errors=errors)
                
            except Exception as e:
                logger.warning(f"MIME type detection failed: {e}")
                mime_type = None
        else:
            logger.debug("MIME type detection skipped (python-magic not available)")
        
        # Scan for malicious content
        is_safe, scan_errors = self._scan_content(file_content)
        
        if not is_safe:
            errors.extend(scan_errors)
            return FileValidationResult(is_valid=False, errors=errors)
        
        logger.info(f"File validated successfully: {safe_filename} ({file_size} bytes)")
        
        return FileValidationResult(
            is_valid=True,
            errors=[],
            safe_filename=safe_filename,
            file_size=file_size,
            mime_type=mime_type
        )
    
    def _get_extension(self, filename: str) -> Optional[str]:
        """
        Get file extension
        
        Args:
            filename: Filename to extract extension from
        
        Returns:
            Extension without dot, or None
        """
        if '.' not in filename:
            return None
        
        return filename.rsplit('.', 1)[1].lower()
    
    def _scan_content(self, content: bytes) -> Tuple[bool, list]:
        """
        Scan file content for malicious patterns
        
        Args:
            content: File content as bytes
        
        Returns:
            Tuple of (is_safe, errors)
        """
        errors = []
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in content.lower():
                errors.append("File contains potentially malicious content")
                logger.warning(f"Malicious pattern detected: {pattern}")
                return False, errors
        
        return True, []
    
    def validate_extension(self, filename: str) -> bool:
        """
        Quick extension validation
        
        Args:
            filename: Filename to validate
        
        Returns:
            True if extension is allowed
        """
        extension = self._get_extension(filename)
        return extension in self.ALLOWED_EXTENSIONS if extension else False


# Global file validator instance
file_validator = FileValidator()
