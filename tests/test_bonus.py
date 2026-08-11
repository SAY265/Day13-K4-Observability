from __future__ import annotations

import json

from app import audit
from app import incidents
from app.mock_llm import FakeLLM


def test_cost_spike_output_is_capped(monkeypatch) -> None:
    monkeypatch.setenv("COST_OPTIMIZATION_ENABLED", "true")
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "120")
    incidents.STATE["cost_spike"] = True
    try:
        response = FakeLLM().generate("short prompt")
    finally:
        incidents.STATE["cost_spike"] = False
    assert response.usage.output_tokens <= 120


def test_audit_record_writes_separate_jsonl(tmp_path, monkeypatch) -> None:
    path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(path))
    audit.record("config_changed", path="config/slo.yaml", summary="bonus test")
    event = json.loads(path.read_text(encoding="utf-8"))
    assert event["event"] == "config_changed"
    assert event["path"] == "config/slo.yaml"
