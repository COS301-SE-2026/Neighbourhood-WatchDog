from __future__ import annotations

import sys


def main() -> int:
    if "--benchmark" in sys.argv:
        from services.benchmark_runner import main as benchmark_main

        benchmark_args = [
            argument
            for argument in sys.argv[1:]
            if argument != "--benchmark"
        ]

        return benchmark_main(benchmark_args)

    import logging
    import uvicorn

    from app import app

    logging.basicConfig(level=logging.INFO)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        access_log=False,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())