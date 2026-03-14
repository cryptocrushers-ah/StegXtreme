from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey
)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os

def generate_keypair():
    """
    Generate a fresh X25519 keypair.
    Returns (private_key, public_bytes)
    """
    private_key  = X25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return private_key, public_bytes


def derive_session_key(
    my_private,
    peer_public: bytes,
    session_id: str
) -> bytes:
    """
    Derive a 32-byte session key using X25519 + HKDF.
    Each session generates fresh keys.
    Old keys deleted after handshake.
    """
    # load peer public key from raw bytes
    peer_public_key = X25519PublicKey.from_public_bytes(peer_public)

    # perform DH exchange
    shared_secret = my_private.exchange(peer_public_key)

    # derive key using HKDF with session_id as salt
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=session_id.encode(),
        info=b"stegxtreme-session"
    ).derive(shared_secret)

    return derived_key