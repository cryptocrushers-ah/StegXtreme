from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey
)
from cryptography.hazmat.primitives import serialization

def generate_signing_keypair():
    """
    Generate Ed25519 signing keypair.
    Returns (private_key, public_key_bytes)
    """
    private_key  = Ed25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return private_key, public_bytes

def sign_data(private_key, data: bytes) -> bytes:
    """Sign data with Ed25519 private key"""
    return private_key.sign(data)

def verify_signature(
    public_key_bytes: bytes,
    signature: bytes,
    data: bytes
) -> bool:
    """Verify Ed25519 signature"""
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature, data)
        return True
    except Exception:
        return False
