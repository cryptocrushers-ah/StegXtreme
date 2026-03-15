import argon2.low_level

def derive_key(password: str, salt: bytes) -> bytes:
    """Derives a 32-byte key from a password and salt using Argon2id."""
    return argon2.low_level.hash_secret_raw(
        secret=password.encode('utf-8'),
        salt=salt,
        time_cost=2,
        memory_cost=65536,
        parallelism=1,
        hash_len=32,
        type=argon2.low_level.Type.ID
    )
