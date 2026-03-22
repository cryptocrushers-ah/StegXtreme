import pytest
import numpy as np
from core.analysis.image import _chi_square_score, _sample_pairs_score
from core.analysis.video import _chi_square_lsb

def test_chi_square_proximity_logic():
    # Test case: Perfectly uniform pairs (embedded)
    embedded_data = np.repeat(np.arange(128, dtype=np.uint8), 100)
    score = _chi_square_score(embedded_data)
    # p-value for zero chi-square is 1.0 -> Score 1.0 (Suspicious)
    assert score > 0.9
    
    # Test case: Random data (not embedded)
    random_data = np.random.randint(0, 256, 12800, dtype=np.uint8)
    score = _chi_square_score(random_data)
    # Natural variations shouldn't exceed the 0.999 threshold
    assert score < 0.1

def test_image_lsb_noise_proximity_logic():
    # Test case: Extremely close to 0.5 (e.g. 0.5001)
    # This should be flagged as suspicious
    embedded_lsb = np.array([0]*5001 + [1]*4999, dtype=np.uint8)
    score = _sample_pairs_score(embedded_lsb)
    # abs(0.5001 - 0.5) * 200 = 0.02 -> Score 1 - 0.02 = 0.98
    assert score > 0.9
    
    # Test case: Natural deviation (e.g. 0.493)
    # This should be considered clean
    natural_lsb = np.array([0]*507 + [1]*493, dtype=np.uint8)
    score = _sample_pairs_score(natural_lsb)
    # abs(0.493 - 0.5) * 200 = 1.4 -> Score 1.0 - 1.0 = 0
    assert score < 0.01
