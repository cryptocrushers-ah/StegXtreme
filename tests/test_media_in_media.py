import os
import pytest
import numpy as np
import cv2
import soundfile as sf
from core.backends.image import ImageBackend
from core.backends.video import VideoBackend
from core.backends.audio import AudioBackend

@pytest.fixture
def sample_image(tmp_path):
    img_path = tmp_path / "cover.png"
    img = np.random.randint(0, 256, (1024, 1024, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), img)
    return str(img_path)

@pytest.fixture
def secret_image(tmp_path):
    img_path = tmp_path / "secret.png"
    img = np.random.randint(0, 256, (8, 8, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), img)
    return str(img_path)

def test_picture_in_picture(sample_image, secret_image, tmp_path):
    stego_path = str(tmp_path / "stego_pip.png")
    password = "pip_password"
    
    with open(secret_image, "rb") as f:
        secret_bytes = f.read()
    
    # Embed
    ImageBackend.embed(
        cover_path=sample_image,
        out_path=stego_path,
        payload=secret_bytes,
        password=password
    )
    
    # Extract
    extracted_bytes = ImageBackend.extract(
        stego_path=stego_path,
        password=password
    )
    
    assert extracted_bytes == secret_bytes
    
    # Verify it can be opened as an image
    extracted_img_path = str(tmp_path / "extracted_secret.png")
    with open(extracted_img_path, "wb") as f:
        f.write(extracted_bytes)
    
    extracted_img = cv2.imread(extracted_img_path)
    assert extracted_img is not None
    assert extracted_img.shape == (8, 8, 3)

def test_audio_in_image(sample_image, tmp_path):
    audio_path = str(tmp_path / "secret.wav")
    samplerate = 44100
    # 0.01 seconds of audio
    data = np.random.uniform(-1, 1, samplerate // 100).astype(np.float32)
    sf.write(audio_path, data, samplerate)
    
    with open(audio_path, "rb") as f:
        secret_bytes = f.read()
    
    stego_path = str(tmp_path / "stego_aii.png")
    password = "aii_password"
    
    # Embed
    ImageBackend.embed(
        cover_path=sample_image,
        out_path=stego_path,
        payload=secret_bytes,
        password=password
    )
    
    # Extract
    extracted_bytes = ImageBackend.extract(
        stego_path=stego_path,
        password=password
    )
    
    assert extracted_bytes == secret_bytes
