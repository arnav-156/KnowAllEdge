"""
Encryption Service for Data at Rest
GDPR Article 32: Security of processing
Implements AES-256 encryption for sensitive data
"""

import os
import base64
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Encryption service for data at rest
    Uses AES-256 encryption via Fernet (symmetric encryption)
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service
        
        Args:
            encryption_key: Base64-encoded encryption key (generates new if not provided)
        """
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # Generate key from environment or create new
            self.key = self._get_or_create_key()
        
        self.fernet = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """
        Get encryption key from environment or generate new one
        
        Returns:
            Encryption key
        """
        # Try to get from environment
        env_key = os.getenv('ENCRYPTION_KEY')
        if env_key:
            return env_key.encode()
        
        # Generate new key
        key = Fernet.generate_key()
        logger.warning("Generated new encryption key. Store this securely!")
        logger.warning(f"ENCRYPTION_KEY={key.decode()}")
        return key
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key
        
        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generates new if not provided)
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext data
        
        Args:
            plaintext: Data to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        if not plaintext:
            return plaintext
        
        try:
            encrypted = self.fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt encrypted data
        
        Args:
            ciphertext: Base64-encoded encrypted data
            
        Returns:
            Decrypted plaintext
        """
        if not ciphertext:
            return ciphertext
        
        try:
            decrypted = self.fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing data
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted fields
        """
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing encrypted data
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with decrypted fields
        """
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(decrypted_data[field])
        
        return decrypted_data
    
    @staticmethod
    def hash_data(data: str) -> str:
        """
        Create SHA-256 hash of data (one-way, for comparison)
        
        Args:
            data: Data to hash
            
        Returns:
            Hex-encoded hash
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_encryption(self) -> bool:
        """
        Verify encryption/decryption works correctly
        
        Returns:
            True if encryption works, False otherwise
        """
        try:
            test_data = "test_encryption_verification"
            encrypted = self.encrypt(test_data)
            decrypted = self.decrypt(encrypted)
            return decrypted == test_data
        except Exception as e:
            logger.error(f"Encryption verification failed: {e}")
            return False


# Utility functions for field-level encryption
def encrypt_sensitive_fields(data: dict, encryption_service: EncryptionService) -> dict:
    """
    Encrypt sensitive fields in user data
    
    Args:
        data: User data dictionary
        encryption_service: Encryption service instance
        
    Returns:
        Dictionary with encrypted sensitive fields
    """
    sensitive_fields = ['email', 'phone', 'address', 'ssn', 'credit_card']
    return encryption_service.encrypt_dict(data, sensitive_fields)


def decrypt_sensitive_fields(data: dict, encryption_service: EncryptionService) -> dict:
    """
    Decrypt sensitive fields in user data
    
    Args:
        data: User data dictionary with encrypted fields
        encryption_service: Encryption service instance
        
    Returns:
        Dictionary with decrypted sensitive fields
    """
    sensitive_fields = ['email', 'phone', 'address', 'ssn', 'credit_card']
    return encryption_service.decrypt_dict(data, sensitive_fields)
