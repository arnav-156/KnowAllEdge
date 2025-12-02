"""
Password Hashing Module

Secure password hashing using bcrypt with configurable cost factor
"""

import bcrypt
import os
from typing import Union
from structured_logging import get_logger

logger = get_logger(__name__)


class PasswordHasher:
    """
    Secure password hashing using bcrypt
    
    Provides methods for hashing and verifying passwords with configurable cost factor
    """
    
    def __init__(self, cost_factor: int = None):
        """
        Initialize password hasher
        
        Args:
            cost_factor: bcrypt cost factor (default: 12, min: 12 for security)
        """
        # Get cost factor from environment or use default
        self.cost_factor = cost_factor or int(os.getenv('BCRYPT_COST_FACTOR', '12'))
        
        # Enforce minimum security requirement
        if self.cost_factor < 12:
            logger.warning(f"Cost factor {self.cost_factor} is below recommended minimum (12). Using 12.")
            self.cost_factor = 12
        
        logger.info(f"PasswordHasher initialized with cost factor: {self.cost_factor}")
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password to hash
        
        Returns:
            Hashed password as string
        
        Raises:
            ValueError: If password is empty or None
            Exception: If hashing fails
        """
        if not password:
            raise ValueError("Password cannot be empty or None")
        
        if len(password) > 72:  # bcrypt limitation
            logger.warning("Password length exceeds bcrypt limit (72 bytes), truncating")
            password = password[:72]
        
        try:
            # Convert password to bytes
            password_bytes = password.encode('utf-8')
            
            # Generate salt and hash
            salt = bcrypt.gensalt(rounds=self.cost_factor)
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Convert back to string for storage
            hashed_str = hashed.decode('utf-8')
            
            logger.debug(f"Password hashed successfully with cost factor {self.cost_factor}")
            return hashed_str
            
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise Exception(f"Failed to hash password: {e}")
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password to verify
            hashed_password: Stored hash to verify against
        
        Returns:
            True if password matches hash, False otherwise
        
        Raises:
            ValueError: If password or hash is empty/None
        """
        if not password:
            raise ValueError("Password cannot be empty or None")
        
        if not hashed_password:
            raise ValueError("Hashed password cannot be empty or None")
        
        try:
            # Convert to bytes
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            # Verify password
            is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)
            
            logger.debug(f"Password verification: {'success' if is_valid else 'failed'}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def get_hash_info(self, hashed_password: str) -> dict:
        """
        Extract information from a bcrypt hash
        
        Args:
            hashed_password: bcrypt hash string
        
        Returns:
            Dictionary with hash information
        """
        try:
            if not hashed_password or not hashed_password.startswith('$2'):
                return {'valid': False, 'error': 'Invalid hash format'}
            
            # Parse bcrypt hash format: $2a$12$salt_and_hash
            parts = hashed_password.split('$')
            
            if len(parts) < 4:
                return {'valid': False, 'error': 'Malformed hash'}
            
            algorithm = parts[1]  # 2a, 2b, etc.
            cost = int(parts[2])  # Cost factor
            salt_and_hash = parts[3]  # Salt + hash (22 chars salt + 31 chars hash)
            
            return {
                'valid': True,
                'algorithm': f'${algorithm}$',
                'cost_factor': cost,
                'salt': salt_and_hash[:22] if len(salt_and_hash) >= 22 else None,
                'is_secure': cost >= 12,
                'needs_rehash': cost < self.cost_factor
            }
            
        except Exception as e:
            logger.error(f"Failed to parse hash info: {e}")
            return {'valid': False, 'error': str(e)}
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if a password hash needs to be rehashed (cost factor too low)
        
        Args:
            hashed_password: Existing hash to check
        
        Returns:
            True if hash should be regenerated with higher cost factor
        """
        hash_info = self.get_hash_info(hashed_password)
        
        if not hash_info['valid']:
            return True  # Invalid hashes should be regenerated
        
        return hash_info.get('needs_rehash', False)
    
    def validate_password_strength(self, password: str) -> dict:
        """
        Validate password strength (basic checks)
        
        Args:
            password: Password to validate
        
        Returns:
            Dictionary with validation results
        """
        if not password:
            return {
                'valid': False,
                'score': 0,
                'errors': ['Password is required']
            }
        
        errors = []
        score = 0
        
        # Length check
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        else:
            score += 1
        
        if len(password) >= 12:
            score += 1
        
        # Character variety checks
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if not has_lower:
            errors.append('Password must contain lowercase letters')
        else:
            score += 1
        
        if not has_upper:
            errors.append('Password must contain uppercase letters')
        else:
            score += 1
        
        if not has_digit:
            errors.append('Password must contain numbers')
        else:
            score += 1
        
        if not has_special:
            errors.append('Password must contain special characters')
        else:
            score += 1
        
        # Common password check (basic)
        common_passwords = {
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        }
        
        if password.lower() in common_passwords:
            errors.append('Password is too common')
            score = max(0, score - 2)
        
        # Calculate strength
        if score >= 5 and not errors:
            strength = 'strong'
        elif score >= 3:
            strength = 'medium'
        else:
            strength = 'weak'
        
        return {
            'valid': len(errors) == 0,
            'score': score,
            'strength': strength,
            'errors': errors,
            'suggestions': self._get_password_suggestions(password, errors)
        }
    
    def _get_password_suggestions(self, password: str, errors: list) -> list:
        """
        Generate password improvement suggestions
        
        Args:
            password: Current password
            errors: List of validation errors
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        if len(password) < 12:
            suggestions.append('Use at least 12 characters for better security')
        
        if 'lowercase' in ' '.join(errors):
            suggestions.append('Add lowercase letters (a-z)')
        
        if 'uppercase' in ' '.join(errors):
            suggestions.append('Add uppercase letters (A-Z)')
        
        if 'numbers' in ' '.join(errors):
            suggestions.append('Add numbers (0-9)')
        
        if 'special' in ' '.join(errors):
            suggestions.append('Add special characters (!@#$%^&*)')
        
        if 'common' in ' '.join(errors):
            suggestions.append('Avoid common passwords and dictionary words')
        
        if not suggestions:
            suggestions.append('Consider using a passphrase with multiple words')
        
        return suggestions


# Global password hasher instance
password_hasher = PasswordHasher()


# Convenience functions for backward compatibility
def hash_password(password: str) -> str:
    """
    Hash a password using the global hasher instance
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return password_hasher.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password using the global hasher instance
    
    Args:
        password: Plain text password
        hashed_password: Stored hash
    
    Returns:
        True if password matches
    """
    return password_hasher.verify_password(password, hashed_password)


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength using the global hasher instance
    
    Args:
        password: Password to validate
    
    Returns:
        Validation results
    """
    return password_hasher.validate_password_strength(password)
