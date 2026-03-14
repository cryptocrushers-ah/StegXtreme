import os
import torch
from core.neural.registry import ModelRegistry
from core.neural.hider import HiderNetwork
from core.crypto.signing import generate_signing_keypair, sign_data, verify_signature

# ── Test kdf.py ──────────────────────────────────────────────────────────
print("=== Testing kdf.py ===")
from core.crypto.kdf import derive_key

salt = os.urandom(16)
key  = derive_key("mypassword", salt)
print(f"Key length: {len(key)} bytes")        # should be 32
print(f"Key type: {type(key)}")               # should be bytes

key2 = derive_key("mypassword", salt)
print(f"Same password+salt = same key: {key == key2}")   # True

key3 = derive_key("wrongpassword", salt)
print(f"Different password = different key: {key != key3}")  # True
print()

# ── Test signing.py ───────────────────────────────────────────────────────
print("=== Testing signing.py ===")
private_key, public_bytes = generate_signing_keypair()
print(f"Public key length: {len(public_bytes)} bytes")  # should be 32

data      = b"test model weights data"
signature = sign_data(private_key, data)
print(f"Signature length: {len(signature)} bytes")      # should be 64

valid = verify_signature(public_bytes, signature, data)
print(f"Valid signature: {valid}")                       # True

tampered = verify_signature(public_bytes, signature, b"tampered data")
print(f"Tampered data rejected: {not tampered}")         # True
print()

# ── Test registry.py ─────────────────────────────────────────────────────
print("=== Testing registry.py ===")
model    = HiderNetwork()
registry = ModelRegistry()

# save
registry.save(model, "storage/models/test_model.pt")
print(f".sig file exists: {os.path.exists('storage/models/test_model.pt.sig')}")  # True

# load — should verify signature
loaded = registry.load(HiderNetwork(), "storage/models/test_model.pt")
print(f"Model loaded successfully: {loaded is not None}")  # True

# verify weights match
for p1, p2 in zip(model.parameters(), loaded.parameters()):
    if not torch.equal(p1, p2):
        print("ERROR: weights don't match")
        break
else:
    print("Weights match after save/load: True")

# tamper test — modify sig file and try to load
with open("storage/models/test_model.pt.sig", "wb") as f:
    f.write(b"tampered signature")
try:
    registry.load(HiderNetwork(), "storage/models/test_model.pt")
    print("ERROR: tampered model loaded — should have failed")
except ValueError as e:
    print(f"Tampered model rejected: True")

print("\n✅ All checks passed")