import time
import threading
from numpy import rint
import torch
from core.neural.trainer import GANTrainer
import os
from core.neural.registry import ModelRegistry

class FeedbackEngine:
    def __init__(self):
        self.history        = []
        self.max_history    = 50
        self.threshold      = 0.30
        self.trainer        = None
        self._lock          = threading.Lock()
        self.retrain_count  = 0
        self._retraining    = False

    def record(self, was_detected: bool):
        should_retrain = False
        with self._lock:
            self.history.append({
                "detected"  : was_detected,
                "timestamp" : time.time()
            })
            if len(self.history) > self.max_history:
                self.history.pop(0)
            if self._detection_rate() > self.threshold and not self._retraining:
                self._retraining   = True
                should_retrain     = True

        if should_retrain:
            thread = threading.Thread(
                target=self._retrain_step,
                daemon=True
            )
            thread.start()

    def _detection_rate(self) -> float:
        if not self.history:
            return 0.0
        detected = sum(1 for h in self.history if h["detected"])
        return detected / len(self.history)

    def _trigger_retrain(self):
        pass

    def _retrain_step(self):
        if self.trainer is None:
            self.trainer = GANTrainer()
            registry      = ModelRegistry()
            hider_path    = "storage/models/hider_trained.pt"
            detector_path = "storage/models/detector_trained.pt"
            if os.path.exists(hider_path):
                registry.load_unsigned(
                    self.trainer.hider, hider_path
                )
                print("[FeedbackEngine] Loaded pretrained hider")
            if os.path.exists(detector_path):
                registry.load_unsigned(
                    self.trainer.detector, detector_path
                )
                print("[FeedbackEngine] Loaded pretrained detector")

        cover    = torch.rand(2, 1, 64, 64)
        payloads = torch.rand(2, 1, 64, 64)
        losses   = self.trainer.train_step(cover, payloads)
        with self._lock:
            self.retrain_count += 1
            self._retraining    = False
        print(f"[FeedbackEngine] Retrain #{self.retrain_count} "
            f"d_loss={losses['d_loss']:.4f} "
            f"h_loss={losses['h_loss']:.4f}")

    def detection_rate(self) -> float:
        with self._lock:
            return self._detection_rate()

    def stats(self) -> dict:
        with self._lock:
            return {
                "total_embeds"    : len(self.history),
                "detection_rate"  : self._detection_rate(),
                "retrain_count"   : self.retrain_count,
                "model_improving" : self.retrain_count > 0
            }