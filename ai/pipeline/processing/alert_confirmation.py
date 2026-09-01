"""
Alert gate for DeepSORT tracks. 
Its purpose is to prevent WatchDog from immediately firing an alert just because YOLO detected something once.
"""

from __future__ import annotations


def is_track_ready_to_alert(track, alerted_ids: set, required_consec_frames: int) -> bool:
    """return true once, for a current (confirmed) deepsort track meeting the hit threshold"""

    if required_consec_frames < 1:
        raise ValueError("required_consec_frames must be at least 1")

    if track.track_id in alerted_ids:
        return False

    if not track.is_confirmed() or track.time_since_update > 0:
        return False


    return int(getattr(track, "hits", 0)) >= required_consec_frames
