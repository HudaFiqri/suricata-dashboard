"""
Encryption/decryption utilities for agent communication
"""

from cryptography.fernet import Fernet
import base64
import json
import logging

logger = logging.getLogger(__name__)


class AgentCrypto:
    """Handles encryption/decryption for agent-dashboard communication"""

    def __init__(self, encryption_key: str):
        """
        Initialize crypto with encryption key

        Args:
            encryption_key: Base64-encoded Fernet key from agent registration
        """
        try:
            # Ensure key is bytes
            if isinstance(encryption_key, str):
                key_bytes = encryption_key.encode('utf-8')
            else:
                key_bytes = encryption_key

            self.cipher = Fernet(key_bytes)
            logger.debug("Encryption initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError(f"Invalid encryption key format. Please check your config file or run agent with --fix-key to auto-repair.")

    @staticmethod
    def is_valid_fernet_key(key: str) -> bool:
        """
        Check if a key is valid Fernet format

        Args:
            key: The encryption key to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if isinstance(key, str):
                key_bytes = key.encode('utf-8')
            else:
                key_bytes = key
            Fernet(key_bytes)
            return True
        except Exception:
            return False

    def encrypt_json(self, data: dict) -> str:
        """
        Encrypt JSON data and return base64-encoded string

        Args:
            data: Dictionary to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        try:
            # Convert to JSON string
            json_str = json.dumps(data)

            # Encrypt
            encrypted = self.cipher.encrypt(json_str.encode('utf-8'))

            # Return as base64 string (for JSON transport)
            return base64.b64encode(encrypted).decode('utf-8')

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_json(self, encrypted_data: str) -> dict:
        """
        Decrypt base64-encoded encrypted data and return JSON

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            Decrypted dictionary
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)

            # Decrypt
            decrypted = self.cipher.decrypt(encrypted_bytes)

            # Parse JSON
            return json.loads(decrypted.decode('utf-8'))

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
