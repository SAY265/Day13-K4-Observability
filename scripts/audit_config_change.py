from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.audit import record
from app.cli import configure_utf8_stdio


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Record an auditable config change.")
    parser.add_argument("--path", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()
    record("config_changed", path=args.path, summary=args.summary)
    print("audit event recorded")


if __name__ == "__main__":
    main()
