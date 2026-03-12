import numpy as np

class StrengthScheduler:
    def compute(self, LH: np.ndarray, HL: np.ndarray) -> float:
        """
        Accepts two numpy arrays (wavelet subbands LH and HL).
        Returns float between 8.0 and 40.0.
        Base strength 18.0, scales up if subband std is high.
        """
        std = (float(LH.std()) + float(HL.std())) / 2
        strength = 18.0 + std * 10.0
        return float(np.clip(strength, 8.0, 40.0))