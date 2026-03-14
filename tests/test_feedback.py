import time
import pytest
from core.neural.feedback import FeedbackEngine


def test_feedback_records_detections():
    engine = FeedbackEngine()
    engine.record(True)
    engine.record(False)
    engine.record(True)
    assert len(engine.history) == 3


def test_feedback_detection_rate_correct():
    engine = FeedbackEngine()
    for _ in range(7):
        engine.record(True)
    for _ in range(3):
        engine.record(False)
    assert abs(engine.detection_rate() - 0.7) < 0.01


def test_feedback_max_history_50():
    engine = FeedbackEngine()
    for i in range(60):
        engine.record(i % 2 == 0)
    assert len(engine.history) == 50


def test_feedback_triggers_retrain_at_30pct():
    engine = FeedbackEngine()
    for _ in range(35):
        engine.record(True)
    for _ in range(15):
        engine.record(False)
    
    # directly call retrain step instead of waiting for thread
    engine._retrain_step()
    assert engine.retrain_count > 0

def test_feedback_stats_returns_dict():
    engine = FeedbackEngine()
    engine.record(True)
    stats = engine.stats()
    assert "total_embeds"    in stats
    assert "detection_rate"  in stats
    assert "retrain_count"   in stats
    assert "model_improving" in stats