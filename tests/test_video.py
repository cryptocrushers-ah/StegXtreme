import pytest
import os
import cv2
import numpy as np
from core.backends.video import VideoBackend

@pytest.fixture
def dummy_video(tmp_path):
    # Create a 5-frame dummy video
    filepath = str(tmp_path / "dummy.avi")
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')
    out = cv2.VideoWriter(filepath, fourcc, 30.0, (64, 64))
    
    # Write empty 64x64 blue frames
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    frame[:, :, 0] = 255
    
    for _ in range(5):
        out.write(frame)
    out.release()
    yield filepath
    
def test_video_embed_extract_roundtrip(dummy_video, tmp_path):
    out_path = str(tmp_path / "stego_dummy.avi")
    payload = b"Secret payload representing text or generic file byte arrays"
    password = "secure_password"
    
    # Embed
    result_path = VideoBackend.embed(dummy_video, out_path, payload, password)
    assert os.path.exists(result_path)
    
    # Extract
    extracted = VideoBackend.extract(result_path, password)
    assert extracted == payload

def test_video_extract_wrong_password_fails(dummy_video, tmp_path):
    out_path = str(tmp_path / "stego_dummy.avi")
    payload = b"Secret data"
    password = "right_password"
    wrong_password = "wrong_password"
    
    VideoBackend.embed(dummy_video, out_path, payload, password)
    
    with pytest.raises(ValueError, match="Decryption failed"):
         VideoBackend.extract(out_path, wrong_password)
