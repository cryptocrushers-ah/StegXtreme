import pytest
from core.crypto.kdf import derive_key
from core.crypto.cipher import aes_encrypt, aes_decrypt

def test_kdf_length():
    password = "supersecretpassword"
    salt = b"test_salt"
    key = derive_key(password, salt)
    assert len(key) == 32

def test_kdf_reproducibility():
    password = "supersecretpassword"
    salt = b"test_salt"
    key1 = derive_key(password, salt)
    key2 = derive_key(password, salt)
    assert key1 == key2

def test_aes_encrypt_decrypt_roundtrip():
    key = b'\x00' * 32  # 32 bytes for AES-256
    data = b"Hello world, this is a secret payload!"
    
    encrypted = aes_encrypt(data, key)
    assert encrypted != data
    assert len(encrypted) > len(data)  # Takes into account nonce and mac
    
    decrypted = aes_decrypt(encrypted, key)
    assert decrypted == data

def test_aes_decrypt_wrong_key_fails():
    key = b'\x00' * 32
    wrong_key = b'\x01' * 32
    data = b"Hello world"
    
    encrypted = aes_encrypt(data, key)
    with pytest.raises(Exception): # Usually cryptography raises an InvalidTag exception
         aes_decrypt(encrypted, wrong_key)
