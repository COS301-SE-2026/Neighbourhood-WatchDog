from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import threading
import time

import numpy as np


@dataclass(frozen=True)
class FramePacket:
    sequence: int
    frame: np.ndarray


class AnnotatedFrameBuffer:
    """thread-safe bounded buffer of frames that are already annotated by the AI loop."""

    def __init__(self, max_frames: int = 100) -> None:

        if max_frames < 1:
            raise ValueError("max_frames must be positive")


        self._frames: deque[FramePacket] = deque(maxlen=max_frames)
        self._condition = threading.Condition()
        self._next_sequence = 0


    def append(self, frame: np.ndarray) -> int:
        """appends a defensive copy and return its sequence number."""

        with self._condition:
            sequence = self._next_sequence
            self._next_sequence += 1


            self._frames.append(
                FramePacket(
                    sequence=sequence,
                    frame=frame.copy(),
                )
            )

            self._condition.notify_all()


            return sequence


    def snapshot_through(self, sequence: int) -> list[np.ndarray]:
        """return copies of all buffered frames at or before sequence."""


        with self._condition:
            return [
                packet.frame.copy()
                for packet in self._frames
                if packet.sequence <= sequence
            ]


    def wait_for_after(self, sequence: int, deadline: float) -> tuple[list[np.ndarray], int]:
        """
        Wait for and return frames after sequence.

        Returns:
            A list of frame copies and the latest returned sequence number.
        """
        with self._condition:
            while True:
                packets = [
                    packet
                    for packet in self._frames
                    if packet.sequence > sequence
                ]

                if packets:
                    return (
                        [packet.frame.copy() for packet in packets],
                        packets[-1].sequence
                    )

                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    return [], sequence

                self._condition.wait(timeout=remaining)