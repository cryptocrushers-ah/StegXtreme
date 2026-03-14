import os
import pytest
import numpy as np
import cv2
from core.backends.image import ImageBackend

@pytest.fixture
def sample_image(tmp_path):
    img_path = tmp_path / "cover.png"
    # Create a 256x256 random image
    img = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
    cv2.imwrite(str(img_path), img)
    return str(img_path)

def test_image_embed_extract(sample_image, tmp_path):
    stego_path = str(tmp_path / "stego.png")
    password = "super_secret_password"
    payload = b"Hello world! This is a secret message hidden via DCT."

    res_path = ImageBackend.embed(
        cover_path=sample_image,
        out_path=stego_path,
        payload=payload,
        password=password
    )

    assert os.path.exists(res_path)

    extracted_payload = ImageBackend.extract(
        stego_path=res_path,
        password=password
    )

    assert extracted_payload == payload

def test_image_invalid_password(sample_image, tmp_path):
    stego_path = str(tmp_path / "stego.png")
    password = "super_secret_password"
    payload = b"Secret"

    ImageBackend.embed(
        cover_path=sample_image,
        out_path=stego_path,
        payload=payload,
        password=password
    )

    with pytest.raises(ValueError, match="Decryption failed"):
        ImageBackend.extract(
            stego_path=stego_path,
            password="wrong_password"
        )
