from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from statistics import mean

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

PII_PATTERNS = (
    re.compile(r"[\w.-]+@[\w.-]+\.\w+"),
    re.compile(r"(?:\+84[ .-]?9\d|0\d{2})[ .-]?\d{3}[ .-]?\d{3,4}"),
    re.compile(r"\b\d{12}\b"),
)


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Detect observability anomalies from JSONL logs.")
    parser.add_argument("--log", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--slo", type=Path, default=REPO_ROOT / "config" / "slo.yaml")
    args = parser.parse_args()

    records = load_records(args.log)
    slo = yaml.safe_load(args.slo.read_text(encoding="utf-8"))["slis"]
    responses = [r for r in records if r.get("event") == "response_sent"]
    requests = sum(r.get("event") == "request_received" for r in records)
    failures = sum(r.get("event") == "request_failed" for r in records)
    latencies = [r["latency_ms"] for r in responses if isinstance(r.get("latency_ms"), (int, float))]
    costs = [r["cost_usd"] for r in responses if isinstance(r.get("cost_usd"), (int, float))]
    qualities = [r["quality_score"] for r in responses if isinstance(r.get("quality_score"), (int, float))]
    anomalies: list[str] = []
    # ponytail: max-latency heuristic; use a rolling percentile window when volume warrants it.
    if latencies and max(latencies) > slo["latency_p95_ms"]["objective"]:
        anomalies.append("latency_above_slo")
    if requests and failures / requests * 100 > slo["error_rate_pct"]["objective"]:
        anomalies.append("error_rate_above_slo")
    if sum(costs) > slo["daily_cost_usd"]["objective"]:
        anomalies.append("daily_cost_above_slo")
    if qualities and mean(qualities) < slo["quality_score_avg"]["objective"]:
        anomalies.append("quality_below_slo")
    if any(any(pattern.search(json.dumps(record, ensure_ascii=False)) for pattern in PII_PATTERNS) for record in records):
        anomalies.append("possible_pii_in_log")

    result = {
        "records": len(records),
        "responses": len(responses),
        "total_cost_usd": round(sum(costs), 4),
        "quality_avg": round(mean(qualities), 4) if qualities else 0,
        "anomalies": sorted(set(anomalies)),
        "status": "alert" if anomalies else "ok",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if anomalies else 0


if __name__ == "__main__":
    raise SystemExit(main())
