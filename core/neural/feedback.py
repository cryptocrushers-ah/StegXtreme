import time
import threading
import os
import cv2
import numpy as np

try:
    from numpy import rint
    import torch
    from core.neural.trainer import GANTrainer
    from core.neural.registry import ModelRegistry
    HAS_NEURAL = True
except ImportError:
    HAS_NEURAL = False

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
        with self._lock:
            if getattr(self, '_actually_training', False):
                return
            self._actually_training = True

        try:
            if not HAS_NEURAL:
                return
            if self.trainer is None:
                self.trainer = GANTrainer()
            
            registry      = ModelRegistry()
            hider_path    = "storage/models/hider_trained.pt"
            detector_path = "storage/models/detector_trained.pt"
            
            if os.path.exists(hider_path):
                registry.load_unsigned(self.trainer.hider, hider_path)
            if os.path.exists(detector_path):
                registry.load_unsigned(self.trainer.detector, detector_path)

            print(f"[FeedbackEngine] Starting autonomous retraining (v{self.retrain_count + 1})...")
            
            for step in range(200):
                cover   = torch.rand(4, 1, 64, 64)
                payload = torch.rand(4, 1, 64, 64)
                self.trainer.train_step(cover, payload)
                
                if step % 50 == 0:
                    time.sleep(0.01)

            registry.save(self.trainer.hider, hider_path)
            registry.save(self.trainer.detector, detector_path)
            
            with self._lock:
                self.retrain_count += 1
                self._retraining = False
                self._actually_training = False
                self.history = self.history[-10:] if len(self.history) > 10 else self.history
                
            print(f"[FeedbackEngine] Retraining successful. Model evolved to version {self.retrain_count}")
            
        except Exception as e:
            print(f"[FeedbackEngine] Retraining failed: {e}")
            with self._lock:
                self._retraining = False
                self._actually_training = False

    def evaluate_file(self, path: str) -> bool:
        """Runs the detector on the first frame/patch of a file and records feedback."""
        if not HAS_NEURAL:
            return False
            
        try:
            if self.trainer is None:
                self.trainer = GANTrainer()
                # Load latest weights
                registry = ModelRegistry()
                p = "storage/models/detector_trained.pt"
                if os.path.exists(p):
                    registry.load_unsigned(self.trainer.detector, p)

            # Load image or first frame
            if path.lower().endswith(('.mp4', '.avi', '.mov')):
                cap = cv2.VideoCapture(path)
                ret, frame = cap.read()
                cap.release()
                if not ret: return False
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is None: return False
                gray = img

            # Process for detector (64x64)
            gray = cv2.resize(gray, (64, 64))
            tensor = torch.tensor(gray, dtype=torch.float32).unsqueeze(0).unsqueeze(0) / 255.0
            
            with torch.no_grad():
                prob = self.trainer.detector(tensor.to(self.trainer.device)).item()
            
            was_detected = prob > 0.5
            self.record(was_detected)
            return was_detected
            
        except Exception as e:
            print(f"[FeedbackEngine] Evaluation error: {e}")
            return False

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