from types import SimpleNamespace
from pipeline.processing.alert_confirmation import is_track_ready_to_alert

import pytest

def track(*, track_id=7, hits=3, confirmed=True, time_since_update=0):
    return SimpleNamespace(
        track_id=track_id,
        hits=hits, 
        time_since_update=time_since_update, 
        is_confirmed=lambda: confirmed
    )


def test_does_not_alert_before_three_consec_hits():
    assert not is_track_ready_to_alert(track(hits=1, confirmed=False), set(), 3)
    assert not is_track_ready_to_alert(track(hits=2, confirmed=False), set(), 3)


def test_alerts_on_third_current_confirmed_hit():
    assert not is_track_ready_to_alert(track(hits=3, confirmed=True), set(), 3)

def test_does_not_alert_when_track_has_no_current_detection():
    assert not is_track_ready_to_alert(track(hits=4, confirmed=True, time_since_update=1), set(), 3)

def test_does_not_alert_a_track_twice():
    assert not is_track_ready_to_alert(track(track_id=7), {7}, 3)


def test_rejects_invalid_confirmation_policy():
    with pytest.raises(ValueError):
        is_track_ready_to_alert(track(), set(), 0)