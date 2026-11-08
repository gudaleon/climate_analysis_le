#!/usr/bin/env python3
"""Extract claims inventories to JSON (printed text only; not evidence)."""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path("/home/hatch/workspace/jeremy_wu_redteam/thesis")
OUT = Path("/home/hatch/workspace/jeremy_wu_redteam/executor_runs/wu_grok/pass1/out")

def parse(path, prefix):
    text = path.read_text(encoding="utf-8")
    pat = re.compile(r"^\- \*\*(" + re.escape(prefix) + r"\d+)\.\*\*\s+(.*)$", re.M)
    claims = []
    for m in pat.finditer(text):
        cid, body = m.group(1), m.group(2).strip()
        nums = re.findall(
            r"(?<![A-Za-z])[-+]?(?:\d+\.\d+|\d+)(?:\s*°C|\s*mm|\s*%|\s*days?)?",
            body,
        )
        claims.append({"id": cid, "text": body, "numbers": nums})
    return claims

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c613 = parse(ROOT / "CLAIMS_INVENTORY_613.md", "C")
    cv7 = parse(ROOT / "CLAIMS_INVENTORY_v7.md", "V7-C")
    (OUT / "claims_613.json").write_text(json.dumps(c613, indent=2))
    (OUT / "claims_v7.json").write_text(json.dumps(cv7, indent=2))
    print("613", len(c613), "v7", len(cv7))

if __name__ == "__main__":
    main()
