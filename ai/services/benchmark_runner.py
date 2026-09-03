from __future__ import annotations

import traceback
import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def report(message: str, fraction: float) -> None:
    print(f"PROGRESS:{message}|{fraction}", flush=True)

def main(argv: list[str] | None = None) -> int:#NOSONAR
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--warmup-frames", type=int, required=True)
    parser.add_argument("--duration", type=float, required=True)
    args = parser.parse_args(argv)

    result: dict = {}
    frame_times: list[float] = []

    try:
        import cv2
        import psutil

        try:
            import torch
        except ImportError:
            torch = None

        from pipeline.processing.tracker import Detector

        report("Loading detection model...", 0.0)
        detector = Detector(args.model)

        gpu_available = False
        gpu_name = None
        if torch is not None:
            try:
                if torch.cuda.is_available():
                    gpu_available = True
                    gpu_name = torch.cuda.get_device_name(0)
            except Exception:
                pass

        capture = cv2.VideoCapture(args.video)
        if not capture.isOpened():
            raise RuntimeError(f"Could not open benchmark clip: {args.video}")

        process = psutil.Process()

        try:
            report("Warming up...", 0.05)
            for _ in range(args.warmup_frames):
                ok, frame = capture.read()
                if not ok:
                    break
                detector.process_frame(frame)

            report("Measuring performance...", 0.2)

            peak_memory = 0.0
            peak_cpu_percent = 0.0
            peak_gpu_memory = 0.0

            process.cpu_percent(interval=None)
            start_time = time.monotonic()

            while (time.monotonic() - start_time) < args.duration:
                ok, frame = capture.read()
                if not ok:
                    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                frame_start = time.perf_counter()
                detector.process_frame(frame)
                frame_times.append(time.perf_counter() - frame_start)

                peak_memory = max(
                    peak_memory,
                    process.memory_info().rss / (1024 * 1024),
                )

                peak_cpu_percent = max(
                    peak_cpu_percent,
                    process.cpu_percent(interval=None),
                )

                if torch is not None and gpu_available:
                    peak_gpu_memory = max(
                        peak_gpu_memory,
                        torch.cuda.max_memory_allocated() / (1024 * 1024),
                    )

                elapsed_fraction = (time.monotonic() - start_time) / args.duration
                report(
                    "Measuring performance...",
                    min(0.2 + elapsed_fraction * 0.8, 0.99),
                )
        finally:
            capture.release()

        if not frame_times:
            raise RuntimeError(
                "benchmark clip ended before any frames could be measured."
            )

        frames_processed = len(frame_times)
        duration = sum(frame_times)
        avg_fps = frames_processed / duration if duration > 0 else 0.0
        sorted_times = sorted(frame_times)
        p95_index = min(int(len(sorted_times) * 0.95), len(sorted_times) - 1)
        p95_frame_time = sorted_times[p95_index] * 1000 #milliseconds

        result = {
            "frames_processed": frames_processed,
            "duration": duration,
            "avg_fps": avg_fps,
            "p95_frame_time": p95_frame_time,
            "peak_memory": peak_memory,
            "peak_cpu_percent": peak_cpu_percent,
            "gpu_available": gpu_available,
            "gpu_name": gpu_name,
            "peak_gpu_memory": peak_gpu_memory,
        }

        report("Benchmark complete", 1.0)

    except Exception as error:
        result = {"error": str(error), "traceback": traceback.format_exc()}

    print(f"RESULT:{json.dumps(result)}", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
