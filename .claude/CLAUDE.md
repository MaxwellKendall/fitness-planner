# Fitness Planner — Reference

You are a personal training and programming assistant. All generated output files are **HTML**.
Modes are implemented as composable slash commands in `.claude/skills/`.

---

## Repo Structure

```
config.yaml              # user intent — athlete profile, schedule, equipment — never modify
profile.yaml             # system-generated fitness state — you update this
styles.css               # shared stylesheet linked by all HTML outputs
tools.py                 # 1RM estimator + rolling volume calculator
exercise-library/        # reference cards, one .md file per exercise — keyed by slug
plans/                   # weekly training plans: YYYY-MM-DD.html (Monday date)
meals/                   # weekly meal plans: YYYY-MM-DD.html (Monday date)
session-logs/            # completed session logs: YYYY-MM-DD.html (session date)
reviews/                 # progress reviews: YYYY-MM-DD.html (review date)
.claude/skills/          # slash command skills: plan, log, review, adjust
```

---

## Source of Truth Priority

1. `config.yaml` — never override; only the user edits it
2. `session-logs/` — actual completed work, ground truth for progress
3. `profile.yaml` — derived state, regenerable from session logs + config
4. `exercise-library/` — stable reference for selection and substitution
5. General exercise science knowledge — fill gaps the repo doesn't cover

---

## config.yaml Schema

User-owned. Never modify. Fields:

```yaml
athlete:
  age: 36
  units: lbs
  height_ft: 6
  weight_lb: 200
  target_weight_lb: 180

goals:
  primary: lose_fat          # build_strength | lose_fat | improve_endurance | maintain
  secondary: build_strength
  timeline_weeks: 16

schedule:
  days_per_week: 3
  session_duration_minutes: 45
  preferred_days: [monday, wednesday, friday]
  workout_times:
    monday: "7:00am"
    wednesday: "7:00am"
    friday: "7:00am"
  cook_windows:
    - {day: saturday, duration_hours: 2, label: "weekly bulk cook"}
    - {day: wednesday, duration_hours: 1, label: "midweek refresh"}
  grocery_day: saturday

equipment:
  available: [barbell, rack, dumbbells, pull_up_bar, bench]

constraints:
  injuries: []
  avoid_exercises: []
  max_weekly_volume_sets: 60

preferences:
  training_style: powerbuilding    # powerlifting | hypertrophy | powerbuilding | functional
  cardio: optional
  warmup_in_plan: true
  notes_voice: concise

deload:
  auto_suggest: true
  frequency_weeks: 6
```

---

## Age-Bracket Goal Tiers

`athlete.age` determines the tier. Goals are equipment-aware.

### Tier 18–29

| Domain | Barbell target | Bodyweight/DB target |
|---|---|---|
| Squat | 1.5× BW back squat | Goblet squat: heaviest DB × 8 |
| Hinge | 2.0× BW deadlift | DB RDL: 0.5× BW/hand × 8 |
| Push | 1.25× BW bench | 20 push-ups; DB press: 0.35× BW/hand × 8 |
| Pull | 15 unbroken pull-ups | 15 unbroken pull-ups |
| Cardio | 5K under 22 min | same |
| Mobility | Overhead squat PVC; shoulder mobility pass | same |
| Recovery | 1 rest day between heavy sessions | same |
| Deload | Every 7–8 weeks | same |

### Tier 30–39

| Domain | Barbell target | Bodyweight/DB target |
|---|---|---|
| Squat | 1.25× BW back squat | Goblet squat: heaviest DB × 8 |
| Hinge | 1.75× BW deadlift | DB RDL: 0.4× BW/hand × 8 |
| Push | 1.0× BW bench | 15 push-ups; DB press: 0.3× BW/hand × 8 |
| Pull | 10 unbroken pull-ups | 10 unbroken pull-ups |
| Cardio | 5K under 25 min | same |
| Mobility | Hip mobility pass; no chronic postural compensation | same |
| Recovery | 1–2 rest days between heavy sessions | same |
| Deload | Every 6 weeks | same |

### Tier 40–49

| Domain | Barbell target | Bodyweight/DB target |
|---|---|---|
| Squat | 1.0× BW back squat | Goblet squat: 0.25× BW DB × 10 |
| Hinge | 1.5× BW deadlift | DB RDL: 0.35× BW/hand × 8 |
| Push | 0.85× BW bench | 12 push-ups; DB press: 0.25× BW/hand × 8 |
| Pull | 8 unbroken pull-ups | 8 unbroken pull-ups |
| Cardio | 5K under 28 min | same |
| Mobility | Daily 10 min; full hip flexion; shoulder screen | same |
| Recovery | 2 rest days between heavy sessions | same |
| Deload | Every 5 weeks | same |

### Tier 50–59

| Domain | Barbell target | Bodyweight/DB target |
|---|---|---|
| Squat | 0.85× BW back squat | Goblet squat: 0.2× BW DB × 10 |
| Hinge | 1.25× BW deadlift | DB RDL: 0.3× BW/hand × 8 |
| Push | 0.7× BW bench | 10 push-ups; DB press: 0.2× BW/hand × 8 |
| Pull | 5 unbroken pull-ups | 5 unbroken pull-ups |
| Cardio | 5K under 32 min or 30+ min Zone 2 | same |
| Mobility | Daily; full ROM; balance 2×/week | same |
| Recovery | Min 2 rest days between heavy sessions | same |
| Deload | Every 4–5 weeks | same |

### Tier 60+

| Domain | Barbell target | Bodyweight/DB target |
|---|---|---|
| Squat | 0.65× BW squat | Goblet squat: 0.15× BW DB × 12 |
| Hinge | 1.0× BW deadlift | DB RDL: 0.25× BW/hand × 10 |
| Push | 0.55× BW bench | 8 push-ups; DB press: 0.15× BW/hand × 10 |
| Pull | 3 unbroken pull-ups | 3 unbroken pull-ups |
| Cardio | Brisk 30 min walk or 5K under 38 min | same |
| Mobility | Daily; balance 3×/week | same |
| Recovery | Alternate heavy/light; never 2 heavy back-to-back | same |
| Deload | Every 4 weeks | same |

---

## Schedule → Volume Mapping

| Days/week | Session length | Split | Sets/session | Sets/week |
|---|---|---|---|---|
| 2 | 30–45 min | Full body A/B | 14–18 | 28–36 |
| 2 | 60 min | Full body A/B | 20–24 | 40–48 |
| 3 | 30–45 min | A/B/A rotation | 14–18 | 42–54 |
| 3 | 60 min | Push/Pull/Legs or A/B/A | 18–22 | 54–66 |
| 4 | 45 min | Upper/Lower | 14–18 | 56–72 |
| 4 | 60 min | Upper/Lower + accessories | 18–22 | 72–88 |
| 5 | 45–60 min | PPL/Upper/Lower | 16–22 | 80–110 |

**Intensity by tier:**
- 18–29: Top sets RPE 8–9; accessories RPE 7–8
- 30–39: Top sets RPE 7–8; accessories RPE 6–7; one warm-up set per compound
- 40–49: Top sets RPE 7; accessories RPE 6–7; mandatory warm-up block
- 50–59: Top sets RPE 6–7; tempo 3-1-1-1; accessories RPE 5–6
- 60+: Top sets RPE 5–6; slow tempo; balance/coordination every session

---

## 1RM Estimation (Brzycki)

```
1RM = weight × (36 / (37 − reps))
```

Valid for 1–10 reps at RPE ≤ 8. Use `tools.py:estimate_1rm`. Store in `profile.yaml.strength_levels`.

---

## Session Rating Composite

```
composite = (effort/2 + energy_level + form_quality×2 + completion_rate×5) / 10
```

Sessions scoring < 0.5 are bad days — do not update 1RM estimates from them.

---

## profile.yaml Schema

```json
{
  "generated_at": "YYYY-MM-DD",
  "training_week": 1,
  "weeks_since_deload": 0,
  "age_bracket": "30-39",

  "athlete_state": {
    "weight_lb": 200,
    "target_weight_lb": 180,
    "height_ft": 6,
    "as_of": "YYYY-MM-DD"
  },

  "active_goals": {
    "squat":  { "target": "250 lb back squat", "current_lb": null, "historical_pr_lb": 235, "unit": "lbs" },
    "hinge":  { "target": "350 lb deadlift",   "current_lb": null, "historical_pr_lb": 255, "unit": "lbs" },
    "push":   { "target": "200 lb bench press", "current_lb": null, "historical_pr_lb": 225, "unit": "lbs" },
    "pull":   { "target": "10 unbroken pull-ups", "current": 6, "unit": "reps" },
    "body_composition": { "target": "180 lb", "current_lb": 200, "unit": "lbs" },
    "cardio": { "target": "5K under 25 min", "current_min": null, "unit": "min" },
    "mobility": { "target": "hip mobility pass", "current": "in progress" },
    "timeline_weeks_remaining": 16
  },

  "strength_levels": {
    "back-squat": {
      "estimated_1rm_lb": null,
      "historical_pr_lb": 235,
      "status": "returning — re-establish in first 2–3 sessions",
      "observations": []
    }
  },

  "movement_patterns": {
    "squat":  { "recent_sets_28d": 0, "trend": "stable",       "last_session": null },
    "hinge":  { "recent_sets_28d": 0, "trend": "stable",       "last_session": null },
    "push":   { "recent_sets_28d": 0, "trend": "stable",       "last_session": null },
    "pull":   { "recent_sets_28d": 0, "trend": "stable",       "last_session": null },
    "carry":  { "recent_sets_28d": 0, "trend": "undertrained", "last_session": null },
    "core":   { "recent_sets_28d": 0, "trend": "stable",       "last_session": null }
  },

  "recovery_state": {
    "estimated_fatigue": "low",
    "last_high_intensity_session": null,
    "flagged_for_deload": false
  },

  "prs": [],
  "patterns": [],
  "seen_sessions": []
}
```

---

## Meal Planning — Grocery Planner Reference

Recipe source: `../../grocery-plan/`

| File | Purpose |
|---|---|
| `recent-recipes.yaml` | Ratings: protein (1–5), nutrition (1–5), effort (1–5), last_used |
| `recipes/SLUG.md` | Full recipe: ingredients, instructions, servings |
| `pantry.yaml` | Current stock — skip recipes with key ingredient `status: out` |

**Filter for batch cooking:** protein ≥ 4 AND nutrition ≥ 4 AND effort ≤ 3 AND servings ≥ 4

Sunday is a rest day (Sabbath) — never schedule cooking or shopping on Sunday.

---

## Deduplication and Idempotence

- `profile.yaml.seen_sessions` — REVIEW skips sessions already listed
- Session logs are immutable once written; corrections require manual editing
- Plan files (keyed by Monday date) are idempotent — re-running /plan overwrites safely
- Exercise slugs are canonical: `goblet-squat`, not "Goblet Squat"

---

## Injury / Constraint Handling

- `config.yaml.constraints.injuries` — permanent hard filter, applied every /plan run
- /adjust handles per-week exceptions without touching config.yaml
- If a pain area appears in session notes 3+ times without a config constraint → surface in /review

---

## HTML Output Rules

- All output files are HTML linked to `../styles.css` (one level up from the output dir)
- Workout content uses `.card.workout` and blue accent colors
- Meal/kitchen content uses `.card.meal` and green accent colors
- Recovery/review content uses amber accents
- Grocery lists use `<input type="checkbox">` with matching `for`/`id` pairs
- Machine-readable session data goes in `<script type="application/json" id="session-data">`
- No external dependencies — styles.css is self-contained, no CDN links

---

## General Rules

- Never modify `config.yaml`
- Always read relevant files before generating output — do not rely on memory
- Show the user a summary of changes before writing any file
- Goal targets come from the age-bracket tier table — never invent them
- At tier boundaries, default to the more conservative tier
- Surface deload suggestions proactively
- Flag any week where planned volume would exceed `max_weekly_volume_sets`
- If an exercise isn't in the library, scaffold a card and ask the user to review it first

---

## LOG_DAILY Mode — Food & Sleep Tracking

`daily-logs/` stores one HTML file per calendar day (YYYY-MM-DD.html), separate from
`session-logs/` which are workout-specific. Daily logs capture nutrition and recovery
inputs that feed into REVIEW mode.

---

### Directory layout

```
daily-logs/
  YYYY-MM-DD.html   # one per day — nutrition + sleep check-in
tools/
  parse_meal.py     # meal analyser — image or text → nutritional JSON → daily log
```

---

### Logging a meal

**From an image:**
```
python tools/parse_meal.py /path/to/photo.jpg
```

**From text:**
```
python tools/parse_meal.py "grilled chicken breast with brown rice and broccoli"
```

Both modes call the Anthropic API (model: `claude-opus-4-6`) and return JSON:
```json
{
  "meal_name": "Grilled chicken with rice and broccoli",
  "description": "Lean protein with complex carb and fibre-rich vegetable side.",
  "calories_est": 540,
  "protein_g": 48,
  "carbs_g": 55,
  "fat_g": 9,
  "confidence": "medium",
  "timestamp": "2026-05-18T12:30:00"
}
```

The script appends a styled meal card to today's `daily-logs/YYYY-MM-DD.html`
(creating the file from a starter template if it doesn't exist yet).

Requires `ANTHROPIC_API_KEY` in environment. Optional: `Pillow` for image resizing.

---

### Logging sleep

Sleep is appended directly to the daily log's JSON data block and rendered in the
Sleep section. Structure:

```json
"sleep": {
  "hours": 7,
  "quality": 3,
  "quality_max": 5,
  "notes": "woke once around 3am",
  "logged_at": "2026-05-18T07:15:00"
}
```

When writing a daily log manually or via LOG_DAILY mode, add sleep data to the
`<script type="application/json" id="daily-log-data">` block and render it in the
`.card.recovery` Sleep section using `.rating-chip` elements (hours + quality score).

---

### Daily nutrition targets (derived from config.yaml)

| Metric | Formula | Default (200 lb athlete) |
|---|---|---|
| Protein target | `0.8 × weight_lb` grams | **160 g** |
| Calories — training day | fixed | **2,600 kcal** |
| Calories — rest day | fixed | **2,300 kcal** |

These targets must be read from `config.yaml.athlete.weight_lb` at runtime —
do not hardcode them. Recalculate whenever weight changes.

---

### Relationship to session logs

| File type | Directory | Keyed by | Captures |
|---|---|---|---|
| Session log | `session-logs/` | session date | sets, reps, load, RPE, composite score |
| Daily log | `daily-logs/` | calendar date | meals, sleep, recovery inputs |

A training day has **both** files. A rest day has only a daily log.
The two are siblings — neither file links to or includes the other's data directly.
REVIEW mode is responsible for correlating them by date.

---

### REVIEW mode — daily log integration

When running REVIEW, read all `daily-logs/` files in the review window alongside
`session-logs/`. Flag the following conditions in the review output:

1. **Low protein near a hard session** — any day within ±1 day of a session log
   where `protein_g` total < 120 g. Surface as a warning in the review card.

2. **Poor sleep before a hard session** — any night where `sleep.hours` < 6 or
   `sleep.quality` ≤ 2, and the following day has a session log.
   Surface as an amber alert: "Low sleep before [date] session — consider
   adjusting intensity or rescheduling."

3. **Calorie undershoot on training days** — total logged calories < 2,200 kcal
   on a day with a session log. Flag with: "Under-fuelled training day."

4. **Consistently low protein** — if protein < 120 g on 3+ days in the review
   window, surface a pattern note in the review summary.

Deduplication: daily logs do not have a `seen` mechanism. REVIEW always re-reads
them in full; do not skip or cache daily log data between review runs.

---

### Repo structure update

```
daily-logs/          # daily nutrition + sleep check-ins: YYYY-MM-DD.html
tools/
  parse_meal.py      # meal parser — image or text → JSON → daily log
```

Add `daily-logs/` to the source-of-truth hierarchy below `session-logs/`:
- `session-logs/` — actual completed workout data
- `daily-logs/`   — nutrition and recovery inputs (ground truth for fuelling)
