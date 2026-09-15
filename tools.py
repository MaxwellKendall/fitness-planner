"""
tools.py — live data helpers for fitness-planner.

Exposes two functions used during LOG and REVIEW modes:
  - estimate_1rm: Brzycki 1RM formula from a logged set
  - rolling_volume: sums sets per movement pattern from session-log front matter

No external API required. Operates entirely on local session-logs/ files.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

SESSION_LOGS_DIR = Path(__file__).parent / "session-logs"


def estimate_1rm(args: dict) -> str:
    """
    Estimate one-rep max using the Brzycki formula.

    1RM = weight × (36 / (37 − reps))

    Reliable for reps 1–10 at RPE ≤ 8. Do not use for sets to failure
    or reps > 10 — the formula degrades significantly past that range.

    Args:
        weight_kg (float): Weight lifted in kilograms
        reps (int): Number of reps completed (1–10)

    Returns:
        JSON string with estimated_1rm_kg and formula metadata.
    """
    weight = args.get("weight_kg")
    reps = args.get("reps")

    if weight is None or reps is None:
        return json.dumps({"error": "weight_kg and reps are both required"})

    reps = int(reps)
    weight = float(weight)

    if reps < 1 or reps > 10:
        return json.dumps({
            "error": f"Brzycki formula is only reliable for 1–10 reps (got {reps}). "
                     "Use direct observation for 1RM, or a different formula for higher reps."
        })

    one_rm = weight * (36 / (37 - reps))

    return json.dumps({
        "estimated_1rm_kg": round(one_rm, 1),
        "formula": "Brzycki: weight × (36 / (37 − reps))",
        "input": {"weight_kg": weight, "reps": reps},
        "confidence": "high" if reps <= 6 else "moderate",
        "note": (
            "Conservative estimate. Use sets at RPE ≤ 8 for best accuracy. "
            "Do not update profile.yaml if session composite score < 0.5 (bad day)."
        )
    }, indent=2)


def rolling_volume(args: dict) -> str:
    """
    Sum total sets per movement pattern across session logs from the last N days.

    Reads the `sets_by_pattern` field from YAML front matter in each session log.
    Files missing this field are skipped with a warning (not an error).

    Args:
        days_back (int): Number of days to look back (default: 28)

    Returns:
        JSON string with sets_by_pattern totals, sessions counted, and any skipped files.
    """
    days_back = int(args.get("days_back", 28))
    cutoff = datetime.today() - timedelta(days=days_back)

    if not SESSION_LOGS_DIR.exists():
        return json.dumps({"error": f"session-logs/ directory not found at {SESSION_LOGS_DIR}"})

    pattern_totals: dict[str, int] = {}
    sessions_counted = 0
    sessions_skipped: list[str] = []

    for log_file in sorted(SESSION_LOGS_DIR.glob("*.md")):
        try:
            file_date = datetime.strptime(log_file.stem, "%Y-%m-%d")
        except ValueError:
            continue  # ignore non-date files

        if file_date < cutoff:
            continue

        content = log_file.read_text(encoding="utf-8")

        # Extract YAML front matter
        if not content.startswith("---"):
            sessions_skipped.append(f"{log_file.name}: no front matter")
            continue

        parts = content.split("---", 2)
        if len(parts) < 3:
            sessions_skipped.append(f"{log_file.name}: malformed front matter")
            continue

        try:
            import yaml
            front = yaml.safe_load(parts[1])
        except Exception as exc:
            sessions_skipped.append(f"{log_file.name}: YAML parse error — {exc}")
            continue

        patterns = front.get("sets_by_pattern")
        if not patterns or not isinstance(patterns, dict):
            sessions_skipped.append(f"{log_file.name}: missing sets_by_pattern field")
            continue

        for pattern, sets_count in patterns.items():
            pattern_totals[pattern] = pattern_totals.get(pattern, 0) + int(sets_count)

        sessions_counted += 1

    result = {
        "days_back": days_back,
        "cutoff_date": cutoff.strftime("%Y-%m-%d"),
        "sessions_counted": sessions_counted,
        "sets_by_pattern": pattern_totals,
    }
    if sessions_skipped:
        result["sessions_skipped"] = sessions_skipped

    return json.dumps(result, indent=2)


TOOLS = [
    {
        "name": "estimate_1rm",
        "description": (
            "Estimate one-rep max using the Brzycki formula: 1RM = weight × (36 / (37 − reps)). "
            "Accurate for sets of 1–10 reps at RPE ≤ 8. "
            "Use during LOG mode to record estimated strength, and during REVIEW to update "
            "profile.yaml strength_levels (conservative: only update if new estimate > current)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "weight_kg": {
                    "type": "number",
                    "description": "Weight lifted in kilograms"
                },
                "reps": {
                    "type": "integer",
                    "description": "Number of reps completed (must be 1–10)"
                }
            },
            "required": ["weight_kg", "reps"]
        },
        "fn": estimate_1rm,
    },
    {
        "name": "rolling_volume",
        "description": (
            "Sum total sets per movement pattern across session-logs/ files from the last N days "
            "(default: 28 days = ~4 training weeks). "
            "Reads sets_by_pattern from session front matter. "
            "Use during REVIEW to compute 4-week volume averages for profile.yaml.movement_patterns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "Number of days to look back (default: 28)",
                    "default": 28
                }
            },
            "required": []
        },
        "fn": rolling_volume,
    },
]
