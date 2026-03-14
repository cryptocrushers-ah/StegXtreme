import os
import cv2
import numpy as np
import pytest

from core.visualiser.bitplane import render_bitplanes
from core.visualiser.heatmap import render_heatmap
from core.visualiser.timeline import render_timeline

TEMP_VIDEO = "storage/temp/test_visualiser_video.mp4"
os.makedirs("storage/temp", exist_ok=True)

@pytest.fixture(scope="module")
def dummy_image():
    # 100x100 dummy color image
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

@pytest.fixture(scope="module")
def dummy_video_path():
    # Create a simple 1-second video with 30 frames
    out = cv2.VideoWriter(TEMP_VIDEO, cv2.VideoWriter_fourcc(*'mp4v'), 30, (100, 100))
    for _ in range(30):
        frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        out.write(frame)
    out.release()
    yield TEMP_VIDEO
    # Cleanup
    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)

def test_render_bitplanes(dummy_image):
    b64 = render_bitplanes(dummy_image)
    assert isinstance(b64, str)
    # Check if it has a base64 common start pattern, or just ensure it's not empty
    assert len(b64) > 100
    assert "iVBORw0KGgo" in b64[:50]  # type: ignore[index]  # PNG magic bytes in base64

def test_render_heatmap(dummy_image):
    b64 = render_heatmap(dummy_image)
    assert isinstance(b64, str)
    assert len(b64) > 100
    assert "iVBORw0KGgo" in b64[:50]  # type: ignore[index]

def test_render_timeline(dummy_video_path):
    # Ask for 5 frames to keep the test fast
    b64 = render_timeline(dummy_video_path, n_frames=5)
    assert isinstance(b64, str)
    assert len(b64) > 100
    assert "iVBORw0KGgo" in b64[:50]  # type: ignore[index]

def test_render_timeline_missing_file():
    with pytest.raises(ValueError, match="Video file not found"):
        render_timeline("nonexistent_video.mp4", n_frames=10)
