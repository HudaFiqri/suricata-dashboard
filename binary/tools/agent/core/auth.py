"""
Token Encryption and Authentication
Encrypts agent token before sending to dashboard
"""

import hashlib
import base64
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class TokenEncryptor:
    """Encrypt and decrypt agent tokens"""

    def __init__(self, plain_token, secret_key, agent_id):
        """
        Initialize token encryptor

        Args:
            plain_token: Plain text token from config
            secret_key: Secret key for encryption (shared with dashboard)
            agent_id: Agent ID
        """
        self.plain_token = plain_token
        self.agent_id = agent_id

        # Derive encryption key from secret + agent_id
        key_material = f"{secret_key}:{agent_id}".encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())

        self.fernet = Fernet(key)

    def encrypt(self):
        """
        Encrypt token for transmission

        Returns:
            str: Encrypted token (base64 encoded)
        """
        try:
            encrypted = self.fernet.encrypt(self.plain_token.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt token: {e}")
            return None

    def get_headers(self):
        """
        Get HTTP headers with encrypted token

        Returns:
            dict: Headers for HTTP requests
        """
        encrypted_token = self.encrypt()

        if not encrypted_token:
            return {}

        return {
            'X-Agent-Token': encrypted_token,
            'X-Agent-ID': str(self.agent_id),
            'Content-Type': 'application/json'
        }

    @staticmethod
    def hash_token(plain_token, secret_key):
        """
        Hash token for storage (dashboard-side)

        Args:
            plain_token: Plain text token
            secret_key: Secret key for hashing

        Returns:
            str: Hashed token (hex)
        """
        return hashlib.pbkdf2_hmac(
            'sha256',
            plain_token.encode(),
            secret_key.encode(),
            100000
        ).hex()
