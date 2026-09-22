import hashlib, hmac, secrets
from cryptography.fernet import Fernet
from .config import settings

def fingerprint(value: str) -> str:
    return hmac.new(settings.fingerprint_key.encode(), value.encode(), hashlib.sha256).hexdigest()

def encrypt(value: str) -> str:
    return Fernet(settings.encryption_key.encode()).encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return Fernet(settings.encryption_key.encode()).decrypt(value.encode()).decode()

def hash_token(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def random_token() -> str:
    return secrets.token_urlsafe(48)
