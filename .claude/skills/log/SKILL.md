---
name: log
description: Record a completed training session. Pre-populates from the week's plan if found, collects actual sets/reps/loads, estimates 1RM via Brzycki, and writes session-logs/YYYY-MM-DD.html. Updates profile.yaml.seen_sessions only.
user-invocable: true
---

# /log — Log a Completed Session

Record what actually happened in a training session. Output is HTML.

## Steps

1. **Determine date** — today unless user specifies otherwise.

2. **Find the plan** — check `plans/` for the `.html` file covering this week (Monday date).
   If found, read the session table for today's date and pre-populate the log.
   Ask the user to confirm or correct: actual sets, reps, loads, anything skipped or added.

3. **If no plan exists** — scaffold from the user's description of what they did.

4. **Parse the session**
   - Extract: exercises, sets, reps, loads, notes
   - For each main barbell lift where set was 1–10 reps at RPE ≤ 8:
     call `tools.py:estimate_1rm` (Brzycki: `weight × (36 / (37 − reps))`)
   - Flag any new estimated 1RM higher than profile.yaml.strength_levels as a potential PR

5. **Count sets by movement pattern**
   - squat / hinge / push / pull / carry / core
   - Used by REVIEW to compute rolling volume

6. **Collect session ratings** (ask user if not provided)
   - effort: RPE 1–10 (how hard overall)
   - energy_level: 1–5 (how you felt coming in)
   - form_quality: 1–5 (technique confidence)
   - completion_rate: planned sets completed / total planned sets (compute automatically if plan was found)

7. **Write `session-logs/YYYY-MM-DD.html`**

8. **Update profile.yaml** — append date to `seen_sessions` only.
   Do NOT update strength_levels here — that happens in /review.

9. **Show user the log** and confirm before writing.

---

## Output: `session-logs/YYYY-MM-DD.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Session Log — YYYY-MM-DD</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <header class="site-header log">
    <div class="header-inner">
      <span class="badge" style="background:#ede9fe;color:#7c3aed">Session A</span>
      <h1>YYYY-MM-DD</h1>
      <span class="header-meta">N min · effort N/10 · completion N%</span>
    </div>
    <div class="header-nav">
      <a href="../plans/YYYY-MM-DD.html">← training plan</a>
    </div>
  </header>

  <main>
    <!-- Session ratings -->
    <section class="card">
      <div class="card-header">Session Ratings</div>
      <div class="card-body">
        <div class="ratings-row">
          <div class="rating-chip">
            <span class="chip-val">N</span>
            <span class="chip-label">Effort RPE</span>
          </div>
          <div class="rating-chip">
            <span class="chip-val">N</span>
            <span class="chip-label">Energy</span>
          </div>
          <div class="rating-chip">
            <span class="chip-val">N</span>
            <span class="chip-label">Form</span>
          </div>
          <div class="rating-chip">
            <span class="chip-val">N%</span>
            <span class="chip-label">Completion</span>
          </div>
        </div>
      </div>
    </section>

    <!-- PR alert if applicable -->
    <div class="alert info">
      <strong>Potential PR:</strong> Back Squat estimated 1RM ~XXX lb (Brzycki from N×XXX lb)
    </div>

    <!-- Actual work -->
    <section class="card workout">
      <div class="card-header">Actual Work</div>
      <div class="card-body">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Exercise</th><th>Sets</th><th>Reps</th><th>Load</th><th>Est. 1RM</th><th>Notes</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>Back Squat</td><td>4</td><td>5</td><td>155 lb</td>
                <td><span class="badge pr">~185 lb</span></td>
                <td>RPE 7, depth good</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Sets by pattern (hidden data for REVIEW) -->
    <section class="card">
      <div class="card-header">Volume by Pattern</div>
      <div class="card-body">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Pattern</th><th>Sets</th></tr></thead>
            <tbody>
              <tr><td>Squat</td><td>N</td></tr>
              <tr><td>Hinge</td><td>N</td></tr>
              <tr><td>Push</td><td>N</td></tr>
              <tr><td>Pull</td><td>N</td></tr>
              <tr><td>Carry</td><td>N</td></tr>
              <tr><td>Core</td><td>N</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Notes / response -->
    <section class="card">
      <div class="card-header">Notes</div>
      <div class="card-body">
        <p>Freeform notes here — how it felt, any pain, form cues, wins.</p>
      </div>
    </section>
  </main>

  <!-- Machine-readable metadata for /review parsing -->
  <script type="application/json" id="session-data">
  {
    "date": "YYYY-MM-DD",
    "plan_ref": "plans/YYYY-MM-DD.html",
    "session_label": "Session A",
    "duration_minutes": N,
    "sets_by_pattern": {"squat": N, "hinge": N, "push": N, "pull": N, "carry": N, "core": N},
    "ratings": {"effort": N, "energy_level": N, "form_quality": N, "completion_rate": 1.0},
    "estimated_1rms": [{"exercise": "back-squat", "estimated_lb": N, "from_weight_lb": N, "reps": N}]
  }
  </script>
</body>
</html>
```

Note the `<script type="application/json" id="session-data">` block — /review reads this for structured data instead of parsing prose HTML.
