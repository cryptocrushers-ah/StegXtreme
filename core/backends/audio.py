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
    def embed(cls, cover_path: str, out_path: str, payload: bytes, password: str) -> str:
        data, samplerate = sf.read(cover_path, dtype='int16')
        
        salt = b'StegXtreme_Audio'
        key = derive_key(password, salt)
        
        # Encrypt payload
        encrypted_payload = aes_encrypt(payload, key)
        
        # Prepare bits: 32-bit length + payload bits
        payload_len = len(encrypted_payload)
        length_bytes = np.array([payload_len], dtype='>u4').view(np.uint8)
        
        all_bits = np.concatenate((
            cls._to_bits(length_bytes.tobytes()),
            cls._to_bits(encrypted_payload)
        ))
        
        # Flatten audio data for easier access
        original_shape = data.shape
        flat_data = data.flatten()

        if len(all_bits) > len(flat_data):
            raise ValueError(f"Payload too large. Max capacity {len(flat_data)} bits, required {len(all_bits)} bits.")
            
        # Clear LSB and embed
        flat_data[:len(all_bits)] &= ~1
        flat_data[:len(all_bits)] |= all_bits.astype(np.int16)
        
        # Reshape and write
        stego_data = flat_data.reshape(original_shape)
        sf.write(out_path, stego_data, samplerate, subtype='PCM_16')
        
        return out_path

    @classmethod
    def extract(cls, stego_path: str, password: str) -> bytes:
        data, samplerate = sf.read(stego_path, dtype='int16')
        flat_data = data.flatten()
        
        if len(flat_data) < 32:
            raise ValueError("Audio file too short to contain a payload.")
            
        # Extract 32-bit length
        length_bits = flat_data[:32] & 1
        length_bytes = cls._from_bits(length_bits.astype(np.uint8))
        payload_len = np.frombuffer(length_bytes, dtype='>u4')[0]
        
        total_bits = 32 + payload_len * 8
        if total_bits > len(flat_data):
            raise ValueError("Corrupt header, calculated capacity exceeds audio length.")
            
        # Extract payload bits
        payload_bits = flat_data[32:total_bits] & 1
        encrypted_payload = cls._from_bits(payload_bits.astype(np.uint8))
        
        salt = b'StegXtreme_Audio'
        key = derive_key(password, salt)
        
        try:
             decrypted_payload = aes_decrypt(encrypted_payload, key)
             return decrypted_payload
        except Exception as e:
             raise ValueError("Decryption failed. Incorrect password?") from e
