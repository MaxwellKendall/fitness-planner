---
name: review
description: Analyze recent session logs, update profile.yaml strength levels and movement patterns, evaluate goal progress, and produce a structured HTML progress report.
user-invocable: true
---

# /review — Progress Review + Profile Update

Analyze recent session logs, update profile.yaml, and produce a structured progress report. Output is HTML.

## Steps

1. **Find new sessions**
   - List all files in `session-logs/`
   - Skip dates already in `profile.yaml.seen_sessions`
   - Skip sessions with date ≤ `profile.yaml.generated_at`

2. **Extract session data**
   - Read each new session log HTML file
   - Parse the `<script type="application/json" id="session-data">` block for structured data
   - Fall back to reading the HTML tables if the JSON block is absent

3. **Recompute rolling volume**
   - Count sets per movement pattern across the last 28 days (all session files, not just new ones)
   - Call `tools.py:rolling_volume` if available, otherwise compute manually
   - Update `profile.yaml.movement_patterns.*.recent_sets_28d`
   - Set trend: if this week's sets > 4-week avg → "increasing"; if < avg → "decreasing"; else "stable"
   - Flag any pattern with recent_sets_28d = 0 as "undertrained"

4. **Update strength estimates**
   - For each session, read `estimated_1rms` from session-data JSON
   - Compute session composite score: `(effort/2 + energy_level + form_quality×2 + completion_rate×5) / 10`
   - If composite < 0.5 → skip 1RM updates for this session (bad day)
   - Update `profile.yaml.strength_levels` only if new estimate EXCEEDS current (never regress)
   - Detect PRs: new estimate > any prior → append to `profile.yaml.prs`

5. **Evaluate recovery state**
   - `high` fatigue: 3+ consecutive sessions with effort ≥ 8, OR total weekly volume > max_weekly_volume_sets
   - `low` fatigue: last session effort ≤ 5 AND ≥ 3 days since last session
   - Otherwise: `moderate`
   - Update `profile.yaml.recovery_state`

6. **Evaluate goal progress**
   - Compare `profile.yaml.strength_levels` against age-bracket tier targets
   - Compute % progress toward each goal
   - Push:pull ratio check — flag if > 1.2:1 across the 28-day window

7. **Goal recalibration (every 4 weeks)**
   - Upgrade: completion_rate = 1.0 AND effort < 6 in 3+ consecutive goal-relevant sessions → propose target increment
   - Extend: < 50% goal-relevant sessions completed in 4-week window → propose +4 weeks to timeline
   - Bracket check: if athlete.age crossed a tier boundary → flag and ask user
   - All recalibrations are proposals — confirm with user before updating profile.yaml

8. **Synthesize patterns**
   - Identify recurring pain mentions in session notes
   - If a pain area appears 3+ times without a config constraint → ask user to add one
   - Append observations to `profile.yaml.patterns` with date prefix

9. **Update profile.yaml**
   - Increment `training_week`
   - Increment `weeks_since_deload`
   - Set `generated_at` to today
   - Append all processed session dates to `seen_sessions`

10. **Write `reviews/YYYY-MM-DD.html`** and show the user

---

## Output: `reviews/YYYY-MM-DD.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Review — Week N</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <header class="site-header review">
    <div class="header-inner">
      <span class="badge recovery">Week N Review</span>
      <h1>Progress Report</h1>
      <span class="header-meta">YYYY-MM-DD · Tier 30–39</span>
    </div>
  </header>

  <main>
    <!-- Goal progress bars -->
    <section class="card">
      <div class="card-header">Goal Progress — Tier 30–39</div>
      <div class="card-body">
        <div class="goal-list">
          <div class="goal-row">
            <div class="goal-label">
              <span class="goal-name">Back Squat</span>
              <span class="goal-pct">— lb → 250 lb target · 0%</span>
            </div>
            <div class="progress-track"><div class="progress-fill" style="width:0%"></div></div>
          </div>
          <div class="goal-row">
            <div class="goal-label">
              <span class="goal-name">Pull-ups</span>
              <span class="goal-pct">6 → 10 reps target · 60%</span>
            </div>
            <div class="progress-track"><div class="progress-fill" style="width:60%"></div></div>
          </div>
          <!-- all goals -->
        </div>
      </div>
    </section>

    <!-- Volume by pattern (SVG trend or table) -->
    <section class="card">
      <div class="card-header">Volume — Last 28 Days</div>
      <div class="card-body">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Pattern</th><th>Sets (28d)</th><th>Trend</th><th>Status</th></tr></thead>
            <tbody>
              <tr><td>Squat</td><td>N</td><td>→</td><td>✓</td></tr>
              <tr><td>Carry</td><td>0</td><td>—</td><td class="muted">undertrained</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Recovery state -->
    <section class="card recovery">
      <div class="card-header">Recovery State</div>
      <div class="card-body">
        <p><strong>Fatigue:</strong> low / moderate / high</p>
        <p><strong>Last high-intensity session:</strong> YYYY-MM-DD</p>
      </div>
    </section>

    <!-- PRs if any -->
    <section class="card">
      <div class="card-header">New PRs This Period</div>
      <div class="card-body">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Exercise</th><th>Estimated 1RM</th><th>Date</th></tr></thead>
            <tbody>
              <tr><td>Back Squat</td><td><span class="badge pr">XXX lb</span></td><td>YYYY-MM-DD</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Pattern observations -->
    <section class="card">
      <div class="card-header">Observations</div>
      <div class="card-body">
        <ul style="padding-left:1.25rem;display:flex;flex-direction:column;gap:.4rem;font-size:.9rem;">
          <li>Push:pull ratio is N:1 (target ≤ 1.2:1)</li>
          <li>Carry pattern still undertrained — add farmer carries week N+1</li>
        </ul>
      </div>
    </section>

    <!-- Deload flag if approaching -->
    <div class="alert warning">
      Deload due in N weeks (every 6 weeks per config).
    </div>
  </main>
</body>
</html>
```
