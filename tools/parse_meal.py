#!/usr/bin/env python3
"""
tools/parse_meal.py — meal parser for fitness-planner daily logs.

Accepts either:
  - A path to an image file (jpg/png) — uses Claude vision to analyse the meal
  - A plain-text description (e.g. "grilled chicken breast with rice and broccoli")

Outputs JSON with fields:
  meal_name, description, calories_est, protein_g, carbs_g, fat_g,
  confidence ("high"/"medium"/"low"), timestamp

Then appends the meal entry to today's daily log (daily-logs/YYYY-MM-DD.html),
creating the file from a starter template if it doesn't exist yet.

Usage:
  python tools/parse_meal.py "grilled salmon with quinoa and asparagus"
  python tools/parse_meal.py /path/to/meal-photo.jpg
  python tools/parse_meal.py /path/to/meal-photo.png --meal-name "Breakfast bowl"

Environment:
  ANTHROPIC_API_KEY — required

Dependencies:
  anthropic, Pillow (for image resizing only; not required for text input)
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
DAILY_LOGS_DIR = REPO_ROOT / "daily-logs"
STYLES_PATH = "../styles.css"   # relative from daily-logs/


# ── Anthropic helper ───────────────────────────────────────────────────────────

def get_client():
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: 'anthropic' package not installed. Run: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY environment variable not set.")

    return anthropic.Anthropic(api_key=api_key)


# ── Nutrition estimation ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a registered dietitian assistant. Your job is to estimate
the nutritional content of a meal from either a photo or a text description.

Return ONLY valid JSON — no markdown, no prose, no code fences — with exactly
these fields:
{
  "meal_name": "short descriptive name (4-8 words)",
  "description": "one-sentence description of the meal",
  "calories_est": <integer, total kcal>,
  "protein_g": <integer, grams of protein>,
  "carbs_g": <integer, grams of carbohydrates>,
  "fat_g": <integer, grams of fat>,
  "confidence": "<high|medium|low>"
}

Confidence guidelines:
- high: clear photo or specific text with weights/portions
- medium: reasonable description but portion size estimated
- low: vague description or heavily obscured photo

Be conservative with calorie estimates. Round all macros to the nearest gram."""


def estimate_from_text(client, description: str) -> dict:
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Estimate the nutritional content of this meal:\n\n{description}"
            }
        ]
    )
    return json.loads(message.content[0].text)


def estimate_from_image(client, image_path: Path) -> dict:
    try:
        from PIL import Image
        import io

        img = Image.open(image_path)
        # Resize to max 1024px on the longest side to reduce tokens
        img.thumbnail((1024, 1024), Image.LANCZOS)
        buf = io.BytesIO()
        fmt = "JPEG" if image_path.suffix.lower() in (".jpg", ".jpeg") else "PNG"
        img.save(buf, format=fmt, quality=85)
        image_data = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
        media_type = "image/jpeg" if fmt == "JPEG" else "image/png"
    except ImportError:
        # Pillow not available — read raw bytes and send as-is
        raw = image_path.read_bytes()
        image_data = base64.standard_b64encode(raw).decode("utf-8")
        suffix = image_path.suffix.lower()
        media_type = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Estimate the nutritional content of this meal photo."
                    }
                ],
            }
        ],
    )
    return json.loads(message.content[0].text)


# ── Daily log HTML helpers ─────────────────────────────────────────────────────

LOG_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily Log — {date_label}</title>
  <link rel="stylesheet" href="{styles_path}">
</head>
<body>

<header class="site-header meal">
  <div class="header-inner">
    <span class="badge meal">Daily Log</span>
    <h1>{date_label}</h1>
    <span class="header-meta">nutrition · sleep · recovery</span>
  </div>
  <div class="header-nav">
    <a href="../session-logs/{iso_date}.html">session log →</a>
    <a href="../plans/{monday_date}.html">week plan →</a>
  </div>
</header>

<main>

  <!-- ── Meals ──────────────────────────────────────── -->

  <section class="card meal" id="meals-section">
    <div class="card-header">🥗 Meals</div>
    <div class="card-body" id="meals-body">
      <p class="muted small">No meals logged yet.</p>
    </div>
  </section>

  <!-- ── Sleep ──────────────────────────────────────── -->

  <section class="card recovery" id="sleep-section">
    <div class="card-header">😴 Sleep</div>
    <div class="card-body" id="sleep-body">
      <p class="muted small">No sleep data logged yet.</p>
    </div>
  </section>

  <!-- ── Daily Summary ──────────────────────────────── -->

  <section class="card" id="summary-section">
    <div class="card-header">📊 Daily Summary</div>
    <div class="card-body" id="summary-body">
      <p class="muted small">Summary updates as meals and sleep are logged.</p>
    </div>
  </section>

</main>

<script type="application/json" id="daily-log-data">
{initial_json}
</script>

</body>
</html>
"""

MEAL_CARD_HTML = """\
      <div style="border:1px solid var(--meal-border);border-radius:var(--radius);padding:1rem;margin-bottom:.75rem;background:var(--meal-bg);">
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.25rem;">
          <strong style="color:var(--meal)">{meal_name}</strong>
          <span class="badge meal">{time_label}</span>
        </div>
        <p class="small muted" style="margin-bottom:.5rem">{description}</p>
        <div style="display:flex;gap:1rem;flex-wrap:wrap;font-size:.85rem;">
          <span>🔥 <strong>{calories_est}</strong> kcal</span>
          <span>🥩 <strong>{protein_g}g</strong> protein</span>
          <span>🍚 <strong>{carbs_g}g</strong> carbs</span>
          <span>🫒 <strong>{fat_g}g</strong> fat</span>
          <span class="muted">confidence: {confidence}</span>
        </div>
      </div>"""


def get_monday(date: datetime) -> str:
    """Return the ISO date string for the Monday of the given date's week."""
    monday = date - __import__("datetime").timedelta(days=date.weekday())
    return monday.strftime("%Y-%m-%d")


def load_or_create_log(iso_date: str) -> tuple[Path, str]:
    """Return (log_path, html_content), creating a starter file if needed."""
    log_path = DAILY_LOGS_DIR / f"{iso_date}.html"

    if not log_path.exists():
        date_obj = datetime.strptime(iso_date, "%Y-%m-%d")
        date_label = date_obj.strftime("%a %b %-d, %Y")
        monday = get_monday(date_obj)

        initial_data = {
            "date": iso_date,
            "day_type": "training",   # caller can update; default to training
            "meals": [],
            "sleep": None,
            "targets": {
                "protein_g": 160,     # 0.8 × 200 lb body weight
                "calories_training": 2600,
                "calories_rest": 2300
            }
        }

        html = LOG_TEMPLATE.format(
            date_label=date_label,
            iso_date=iso_date,
            monday_date=monday,
            styles_path=STYLES_PATH,
            initial_json=json.dumps(initial_data, indent=2)
        )
        DAILY_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_path.write_text(html, encoding="utf-8")

    return log_path, log_path.read_text(encoding="utf-8")


def append_meal_to_log(log_path: Path, html: str, meal: dict) -> None:
    """
    Inject the meal HTML card into the meals section and update the JSON data block.
    Replaces the 'No meals logged yet.' placeholder on first entry.
    """
    time_label = datetime.fromisoformat(meal["timestamp"]).strftime("%-I:%M %p")

    card = MEAL_CARD_HTML.format(
        meal_name=meal["meal_name"],
        description=meal["description"],
        calories_est=meal["calories_est"],
        protein_g=meal["protein_g"],
        carbs_g=meal["carbs_g"],
        fat_g=meal["fat_g"],
        confidence=meal["confidence"],
        time_label=time_label,
    )

    # Replace placeholder or append after last card in the meals body
    if '<p class="muted small">No meals logged yet.</p>' in html:
        html = html.replace(
            '<p class="muted small">No meals logged yet.</p>',
            card
        )
    else:
        html = html.replace(
            "</div>\n  </section>\n\n  <!-- ── Sleep",
            f"{card}\n    </div>\n  </section>\n\n  <!-- ── Sleep",
            1
        )

    # Update JSON data block
    json_start = html.index('<script type="application/json" id="daily-log-data">') \
                 + len('<script type="application/json" id="daily-log-data">\n')
    json_end = html.index("\n</script>", json_start)
    data = json.loads(html[json_start:json_end])
    data["meals"].append(meal)
    updated_json = json.dumps(data, indent=2)
    html = html[:json_start] + updated_json + html[json_end:]

    log_path.write_text(html, encoding="utf-8")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parse a meal (image or text) and append to today's daily log."
    )
    parser.add_argument(
        "input",
        help="Path to a meal image (.jpg/.png) OR a plain-text meal description."
    )
    parser.add_argument(
        "--meal-name",
        default=None,
        help="Override the auto-generated meal name."
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Date to log to (YYYY-MM-DD). Defaults to today."
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print JSON result to stdout and exit without writing to log."
    )
    args = parser.parse_args()

    iso_date = args.date or datetime.today().strftime("%Y-%m-%d")
    input_val = args.input
    image_extensions = {".jpg", ".jpeg", ".png"}

    client = get_client()

    # Decide: image or text?
    input_path = Path(input_val)
    if input_path.suffix.lower() in image_extensions and input_path.exists():
        print(f"📷  Analysing image: {input_path.name}", file=sys.stderr)
        result = estimate_from_image(client, input_path)
    else:
        print(f"📝  Estimating from text description…", file=sys.stderr)
        result = estimate_from_text(client, input_val)

    # Augment result
    result["timestamp"] = datetime.now().isoformat(timespec="seconds")
    if args.meal_name:
        result["meal_name"] = args.meal_name

    # Normalise types
    result["calories_est"] = int(result.get("calories_est", 0))
    result["protein_g"]    = int(result.get("protein_g", 0))
    result["carbs_g"]      = int(result.get("carbs_g", 0))
    result["fat_g"]        = int(result.get("fat_g", 0))

    print(json.dumps(result, indent=2))

    if args.json_only:
        return

    # Append to daily log
    log_path, html = load_or_create_log(iso_date)
    append_meal_to_log(log_path, html, result)
    print(f"\n✅  Logged to {log_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
