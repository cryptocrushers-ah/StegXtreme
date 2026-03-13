import os
import pytest
import numpy as np
import soundfile as sf
from core.backends.audio import AudioBackend

@pytest.fixture
def sample_audio(tmp_path):
    audio_path = tmp_path / "cover.wav"
    samplerate = 44100
    # 1 second of random noise
    data = np.random.randint(-32768, 32767, samplerate, dtype=np.int16)
    sf.write(str(audio_path), data, samplerate, subtype='PCM_16')
    return str(audio_path)

def test_audio_embed_extract(sample_audio, tmp_path):
    stego_path = str(tmp_path / "stego.wav")
    password = "audio_password"
    payload = b"Secret message in audio using LSB."
    
    res_path = AudioBackend.embed(
        cover_path=sample_audio,
        out_path=stego_path,
        payload=payload,
        password=password
    )
    
    assert os.path.exists(res_path)
    
    extracted = AudioBackend.extract(stego_path, password)
    assert extracted == payload

def test_audio_invalid_password(sample_audio, tmp_path):
    stego_path = str(tmp_path / "stego.wav")
    password = "audio_password"
    payload = b"Secret message"
    
    AudioBackend.embed(sample_audio, stego_path, payload, password)
    
    with pytest.raises(ValueError, match="Decryption failed"):
        AudioBackend.extract(stego_path, "wrong_password")
