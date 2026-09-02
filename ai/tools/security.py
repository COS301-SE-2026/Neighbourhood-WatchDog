"""This basically just keeps the functions that are responsible for preventing path traversal/injection"""

from pathlib import Path

# Validation helper functions
def _resolve_within(base: Path, candidate: Path, what: str) -> Path:
    """Resolve `candidate` and ensure that it remains within the `base` path. Raise if it would escape"""
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()

    try: 
        candidate_resolved.relative_to(base_resolved)
    except ValueError:
        raise SystemExit(
            f"Refusing to use {what} outside of {base_resolved}"
        )
    return candidate_resolved

def _safe_frame_id(frame_id: str) -> str:
    """Reject frame ids that could be used for path traversal or absolute paths"""
    if not frame_id or frame_id in {".", ".."} or "/" in frame_id or "\\" in frame_id:
        raise ValueError(f"Unsafe frame_id in manifest: {frame_id!r}")
    return frame_id