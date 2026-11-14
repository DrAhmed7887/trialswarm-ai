"""Serverless Modal deployment for TrialSwarm AI (zero-idle-cost public demo URL)."""

from __future__ import annotations

import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir("src", "/root/src")
    .add_local_dir("data", "/root/data")
    .add_local_dir("eval", "/root/eval")
    .add_local_dir("docs", "/root/docs")
)

app = modal.App("trialswarm-ai", image=image)


@app.function(
    max_containers=3,
    scaledown_window=120,
)
@modal.concurrent(max_inputs=20)
@modal.asgi_app()
def web():
    import sys

    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
    from src.web.app import app as fastapi_app

    return fastapi_app
