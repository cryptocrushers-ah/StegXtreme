import numpy as np
import soundfile as sf
from core.crypto.kdf import derive_key
from core.crypto.cipher import aes_encrypt, aes_decrypt

class AudioBackend:
    @classmethod
    def _to_bits(cls, data: bytes) -> np.ndarray:
        return np.unpackbits(np.frombuffer(data, dtype=np.uint8))

    @classmethod
    def _from_bits(cls, bits: np.ndarray) -> bytes:
        return np.packbits(bits).tobytes()

    @classmethod
    def embed(cls, cover_path: str, out_path: str, payload: bytes, password: str, algorithm: str = "default") -> str:
        data, samplerate = sf.read(cover_path)
        
        salt = b'StegXtreme_Audio'
        key = derive_key(password, salt)
        encrypted_payload = aes_encrypt(payload, key)
        
        # Length (32 bits) + data
        bits = np.unpackbits(np.frombuffer(encrypted_payload, dtype=np.uint8))
        length_bits = np.unpackbits(np.array([len(bits)], dtype='>u4').view(np.uint8))
        all_bits = np.concatenate((length_bits, bits))

        if len(all_bits) > data.size:
            raise ValueError(f"Payload too large. Max capacity {data.size} bits, required {len(all_bits)} bits.")

        # LSB embedding on audio samples
        flat_data = data.flatten()
        # Scale float to int representation for LSB if needed, 
        # but soundfile often returns floats. We'll use a simple float LSB-like approach:
        # Transforming to 16-bit PCM for easier LSB
        pcm_data = (flat_data * 32767).astype(np.int16)
        
        pcm_data[:len(all_bits)] &= 0xFFFE
        pcm_data[:len(all_bits)] |= all_bits
        
        # Back to float
        flat_data = pcm_data.astype(np.float32) / 32767.0
        
        stego_data = flat_data.reshape(data.shape)
        sf.write(out_path, stego_data, samplerate)
        return out_path

    @classmethod
    def extract(cls, stego_path: str, password: str, algorithm: str = "default") -> bytes:
        data, samplerate = sf.read(stego_path)
        flat_data = data.flatten()
        pcm_data = (flat_data * 32767).astype(np.int16)
        
        # Read length (32 bits)
        length_bits = pcm_data[:32] & 1
        length_bytes = np.packbits(length_bits)
        payload_len = np.frombuffer(length_bytes, dtype='>u4')[0]
        
        # Read payload
        extracted_bits = pcm_data[32:32+payload_len] & 1
        extracted_bytes = np.packbits(extracted_bits).tobytes()
        
        salt = b'StegXtreme_Audio'
        key = derive_key(password, salt)
        
        try:
             return aes_decrypt(extracted_bytes, key)
        except Exception as e:
             raise ValueError("Decryption failed. Incorrect password?") from e
