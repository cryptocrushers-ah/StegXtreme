import torch
import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

class ModelRegistry:
    def __init__(self):
        # generate signing keypair once
        self._private_key = Ed25519PrivateKey.generate()
        self._public_key  = self._private_key.public_key()

    def save(self, model, path: str):
        torch.save(model.state_dict(), path)
        # sign the saved file
        signature = self._sign_file(path)
        with open(path + ".sig", "wb") as f:
            f.write(signature)
        print(f"Saved to {path}")
        print(f"Signature saved to {path}.sig")

    def load(self, model, path: str):
        # verify signature before loading
        if not self._verify_file(path):
            raise ValueError(f"Model signature invalid for {path}")
        model.load_state_dict(
            torch.load(path, map_location="cpu")
        )
        model.eval()
        return model

    def load_unsigned(self, model, path: str):
        """Load without signature check — for legacy models"""
        model.load_state_dict(
            torch.load(path, map_location="cpu")
        )
        model.eval()
        return model

    def _sign_file(self, path: str) -> bytes:
        digest = self._hash_file(path)
        return self._private_key.sign(digest)

    def _verify_file(self, path: str) -> bool:
        sig_path = path + ".sig"
        if not __import__("os").path.exists(sig_path):
            return False
        with open(sig_path, "rb") as f:
            signature = f.read()
        digest = self._hash_file(path)
        try:
            self._public_key.verify(signature, digest)
            return True
        except Exception:
            return False

    def _hash_file(self, path: str) -> bytes:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.digest()