from __future__ import annotations

import os
from contextlib import nullcontext
from typing import Any

try:
    from langfuse import get_client, observe, propagate_attributes as _propagate_attributes

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False
    _propagate_attributes = None

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyClient:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

    def get_client():
        return _DummyClient()


def get_langfuse_client():
    return get_client()


def propagate_trace_attributes(client: Any, **attributes: Any):
    if hasattr(client, "propagate_attributes"):
        return client.propagate_attributes(**attributes)
    if hasattr(client, "update_current_trace"):
        client.update_current_trace(**attributes)
        return nullcontext()
    if _propagate_attributes is not None:
        return _propagate_attributes(**attributes)
    return nullcontext()


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )
