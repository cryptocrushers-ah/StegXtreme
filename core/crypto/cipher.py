import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore

def aes_encrypt(data: bytes, key: bytes) -> bytes:
    """Encrypts data using AES-256-GCM. Prepend 12-byte nonce to ciphertext."""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext

def aes_decrypt(data: bytes, key: bytes) -> bytes:
    """Decrypts data using AES-256-GCM. Expects 12-byte nonce at the beginning."""
    aesgcm = AESGCM(key)
    nonce = data[:12]  # type: ignore
    ciphertext = data[12:]  # type: ignore
    return aesgcm.decrypt(nonce, ciphertext, None)
