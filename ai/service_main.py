from __future__ import annotations

import logging

import uvicorn

from app import app

#Start uvicorn for fastAPI app
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        access_log=False,
    )