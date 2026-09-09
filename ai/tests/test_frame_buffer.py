import numpy as np

from ai.pipeline.utils.frame_buffer import AnnotatedFrameBuffer


def test_append_and_snapshot_through_preserve_order():
    buffer = AnnotatedFrameBuffer(max_frames=3)

    first = np.full((2, 2, 3), 1, dtype=np.uint8)
    second = np.full((2, 2, 3), 2, dtype=np.uint8)

    first_sequence = buffer.append(first)
    second_sequence = buffer.append(second)

    frames = buffer.snapshot_through(second_sequence)

    assert first_sequence == 0
    assert second_sequence == 1

    assert len(frames) == 2

    assert np.array_equal(frames[0], first)
    assert np.array_equal(frames[1], second)


def test_snapshot_returns_copies():
    buffer = AnnotatedFrameBuffer(max_frames=2)

    original = np.full((2, 2, 3), 5, dtype=np.uint8)
    sequence = buffer.append(original)

    snapshot = buffer.snapshot_through(sequence)
    snapshot[0][0, 0] = 99

    later_snapshot = buffer.snapshot_through(sequence)

    assert int(later_snapshot[0][0, 0, 0]) == 5


def test_buffer_is_bounded():
    buffer = AnnotatedFrameBuffer(max_frames=2)

    buffer.append(np.full((1, 1, 3), 1, dtype=np.uint8))
    buffer.append(np.full((1, 1, 3), 2, dtype=np.uint8))
    latest_sequence = buffer.append(

        np.full((1, 1, 3), 3, dtype=np.uint8)

    )

    frames = buffer.snapshot_through(latest_sequence)

    assert len(frames) == 2
    assert frames[0][0, 0, 0] == 2
    assert frames[1][0, 0, 0] == 3


def test_wait_for_after_returns_frames_after_sequence():
    buffer = AnnotatedFrameBuffer(max_frames=3)

    trigger_sequence = buffer.append(

        np.full((1, 1, 3), 1, dtype=np.uint8)

    )

    buffer.append(

        np.full((1, 1, 3), 2, dtype=np.uint8)


    )

    frames, latest_sequence = buffer.wait_for_after(
        trigger_sequence,
        deadline=9999999999
    )

    assert len(frames) == 1
    
    assert frames[0][0, 0, 0] == 2

    assert latest_sequence == trigger_sequence + 1