import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.fernet import Fernet
from flask import current_app

def _get_fernet_key(secret_key: str = None) -> bytes:
    """Derive a 32-byte URL-safe base64 key for Fernet from application SECRET_KEY."""
    if not secret_key:
        try:
            secret_key = current_app.config.get('SECRET_KEY')
        except Exception:
            pass
    if not secret_key:
        secret_key = 'default-dev-secret-key-32bytes-min!'
    digest = hashlib.sha256(secret_key.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)

def generate_issuer_keypair():
    """
    Generate Ed25519 keypair for an approved issuer institution.
    Returns tuple: (public_key_pem: str, encrypted_private_key: str, key_id: str)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Serialize Public Key to PEM
    public_pem_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_key_pem = public_pem_bytes.decode('utf-8')
    
    # Serialize Private Key to PKCS8 PEM
    private_pem_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Encrypt private key at rest using Fernet
    try:
        secret_key = current_app.config.get('SECRET_KEY')
    except Exception:
        secret_key = 'default-dev-secret-key-32bytes-min!'
    f = Fernet(_get_fernet_key(secret_key))
    encrypted_private_key = f.encrypt(private_pem_bytes).decode('utf-8')
    
    # Compute Key ID (SHA-256 hex digest of public key PEM)
    key_id = hashlib.sha256(public_pem_bytes).hexdigest()[:16]
    
    return public_key_pem, encrypted_private_key, key_id

def sign_content_hash(encrypted_private_key: str, content_hash: str) -> str:
    """
    Sign a certificate content hash (64-char hex) using issuer's Ed25519 private key.
    Returns base64 encoded signature string.
    """
    try:
        secret_key = current_app.config.get('SECRET_KEY')
    except Exception:
        secret_key = 'default-dev-secret-key-32bytes-min!'
    f = Fernet(_get_fernet_key(secret_key))
    private_pem_bytes = f.decrypt(encrypted_private_key.encode('utf-8'))
    
    private_key = serialization.load_pem_private_key(private_pem_bytes, password=None)
    signature_bytes = private_key.sign(content_hash.encode('utf-8'))
    
    return base64.b64encode(signature_bytes).decode('utf-8')

def verify_signature(public_key_pem: str, content_hash: str, signature_b64: str) -> bool:
    """
    Verify Ed25519 digital signature of content hash using issuer's public key PEM.
    Returns True if valid, False otherwise.
    """
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        signature_bytes = base64.b64decode(signature_b64.encode('utf-8'))
        public_key.verify(signature_bytes, content_hash.encode('utf-8'))
        return True
    except Exception:
        return False
