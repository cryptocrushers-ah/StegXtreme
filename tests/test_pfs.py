import pytest
from core.crypto.pfs import generate_keypair, derive_session_key

def test_pfs_generates_keypair():
    private_key, public_bytes = generate_keypair()
    assert private_key  is not None
    assert len(public_bytes) == 32  # X25519 public keys are 32 bytes

def test_pfs_public_bytes_are_32_bytes():
    _, pub = generate_keypair()
    assert isinstance(pub, bytes)
    assert len(pub) == 32

def test_pfs_both_sides_derive_same_key():
    # simulate two parties exchanging keys
    priv_a, pub_a = generate_keypair()
    priv_b, pub_b = generate_keypair()

    session_id = "test-session-123"

    key_a = derive_session_key(priv_a, pub_b, session_id)
    key_b = derive_session_key(priv_b, pub_a, session_id)

    assert key_a == key_b, "Both sides must derive identical key"

def test_pfs_two_sessions_get_different_keys():
    priv_a, pub_a = generate_keypair()
    priv_b, pub_b = generate_keypair()

    key_1 = derive_session_key(priv_a, pub_b, "session-1")
    key_2 = derive_session_key(priv_a, pub_b, "session-2")

    assert key_1 != key_2, "Different sessions must produce different keys"

def test_pfs_key_is_32_bytes():
    priv_a, pub_a = generate_keypair()
    priv_b, pub_b = generate_keypair()
    key = derive_session_key(priv_a, pub_b, "session-abc")
    assert len(key) == 32

def test_pfs_different_keypairs_different_secrets():
    priv_a, pub_a = generate_keypair()
    priv_b, pub_b = generate_keypair()
    priv_c, pub_c = generate_keypair()

    key_ab = derive_session_key(priv_a, pub_b, "session-1")
    key_ac = derive_session_key(priv_a, pub_c, "session-1")

    assert key_ab != key_ac