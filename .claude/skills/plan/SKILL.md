---
name: plan
description: Generate this week's training plan and meal plan. Reads config.yaml, profile.yaml, exercise-library/, and grocery-plan recipes. Outputs plans/YYYY-MM-DD.html and meals/YYYY-MM-DD.html.
user-invocable: true
---

# /plan — Weekly Training + Meal Plan

Generate this week's workout plan, meal plan, and weekly schedule. All output is HTML.

## Steps

1. **Read inputs**
   - `config.yaml` — athlete, schedule (incl. workout_times, cook_windows, grocery_day), equipment, constraints, style, deload
   - `profile.yaml` — strength levels, movement pattern balance, recovery state, weeks_since_deload, active goals
   - `exercise-library/` — available exercises filtered to equipment.available

2. **Determine tier and targets**
   - Read `athlete.age` → assign Age-Bracket Goal Tier (see CLAUDE.md)
   - Filter targets to `equipment.available` (barbell targets if barbell+rack present)
   - Note current vs. target for each goal (from profile.yaml.active_goals)

3. **Determine split and volume**
   - Use Schedule → Volume Mapping table (CLAUDE.md) with days_per_week × session_duration_minutes
   - 3 days × 45 min = A/B/A full-body rotation, 14–18 sets/session, 42–54 sets/week target

4. **Check deload**
   - If `profile.yaml.weeks_since_deload >= deload.frequency_weeks`: flag as deload week
   - Reduce sets 40–50%, loads 10–15%, cap RPE at 6
   - Add deload alert banner to HTML output

5. **Balance movement patterns**
   - Read `profile.yaml.movement_patterns`
   - Any pattern with `trend: undertrained` → increase its share of planned sets
   - Current: carry is undertrained — add farmer carries or suitcase carries

6. **Select exercises**
   - Filter exercise-library/ by equipment.available and constraints.avoid_exercises
   - Deprioritize exercises used in last 2 session logs
   - Exclude any exercise targeting an injured area from constraints.injuries
   - Returning athlete (weeks 1–2): RPE ceiling 6–7, technique focus, use working sets to estimate 1RM via Brzycki

7. **Assign sets by training style**
   - powerbuilding: ~60% compound low reps (3–6), ~40% accessory higher reps (8–15)
   - Include warm-up sets if preferences.warmup_in_plan = true

8. **Meal planning**
   - Read `../../grocery-plan/recent-recipes.yaml`
   - Filter: protein ≥ 4 AND nutrition ≥ 4 AND effort ≤ 3 AND servings ≥ 4
   - Deprioritize recipes with last_used within prior 2 weeks
   - Cross-check `../../grocery-plan/pantry.yaml` — skip recipes where a key ingredient is `status: out`
   - Select recipes to cover lunches + dinners across cook windows:
     - Saturday bulk cook (2 hrs): 2–3 recipes covering Mon–Fri lunches + Mon–Wed dinners
     - Wednesday midweek refresh (1 hr): 1–2 recipes covering Thu–Fri dinners
   - For each selected recipe, note: name, servings, protein rating, effort rating, relative path to recipe file

9. **Build weekly schedule**
   - 7-day grid: workout slots (from workout_times), cook windows (from cook_windows), grocery run (grocery_day)
   - Saturday = grocery morning + bulk cook afternoon

10. **Build grocery list**
    - Identify ingredients needed for selected recipes
    - Cross-check pantry.yaml — omit anything currently `status: stocked`
    - Group by store section (Produce, Meat & Seafood, Dairy, Dry Goods, etc.)

11. **Write output files**
    - `plans/YYYY-MM-DD.html` (Monday date)
    - `meals/YYYY-MM-DD.html` (same Monday date)

12. **Show user both files and ask for adjustments** before finalizing

---

## Output: `plans/YYYY-MM-DD.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Week N Training Plan</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <header class="site-header workout">
    <div class="header-inner">
      <span class="badge workout">Week N</span>
      <h1>Training Plan</h1>
      <span class="header-meta">Mon DD – Sun DD, YYYY · Tier 30–39 · ~N sets</span>
    </div>
    <div class="header-nav">
      <a href="PREV.html">← prev week</a>
      <a href="../meals/YYYY-MM-DD.html">meal plan →</a>
    </div>
  </header>

  <main>
    <!-- Deload alert if applicable -->
    <div class="alert warning">Deload week — volume reduced 40%, RPE cap 6</div>

    <!-- Active goals with progress bars -->
    <section class="card">
      <div class="card-header workout">Active Goals — Tier 30–39</div>
      <div class="card-body">
        <div class="goal-list">
          <div class="goal-row">
            <div class="goal-label">
              <span class="goal-name">Back Squat</span>
              <span class="goal-pct">current: — · target: 250 lb</span>
            </div>
            <div class="progress-track"><div class="progress-fill" style="width: 0%"></div></div>
          </div>
          <!-- repeat for each goal -->
        </div>
      </div>
    </section>

    <!-- Session A -->
    <section class="card workout">
      <div class="card-header">Monday, YYYY-MM-DD — Session A</div>
      <div class="card-body">
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Exercise</th><th>Sets</th><th>Reps</th><th>Load</th><th>Notes</th></tr>
            </thead>
            <tbody>
              <tr><td>Back Squat</td><td>4</td><td>4</td><td>135 lb</td><td>RPE 6 — re-baseline</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Repeat for Session B, Session C -->

    <!-- Volume summary -->
    <section class="card">
      <div class="card-header">Volume Summary</div>
      <div class="card-body">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Pattern</th><th>Sets This Week</th><th>4-Week Avg</th><th>Status</th></tr></thead>
            <tbody>
              <tr><td>Squat</td><td>N</td><td>N</td><td>✓</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </main>
</body>
</html>
```

---

## Output: `meals/YYYY-MM-DD.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Week N Meal Plan</title>
  <link rel="stylesheet" href="../styles.css">
</head>
<body>
  <header class="site-header meal">
    <div class="header-inner">
      <span class="badge meal">Week N</span>
      <h1>Meal Plan</h1>
      <span class="header-meta">Recomp focus · high protein · batch cook</span>
    </div>
    <div class="header-nav">
      <a href="../plans/YYYY-MM-DD.html">training plan →</a>
    </div>
  </header>

  <main>
    <!-- 7-day schedule grid -->
    <section class="card">
      <div class="card-header meal">Weekly Schedule</div>
      <div class="card-body">
        <div class="week-grid">
          <div class="day-cell workout-day">
            <span class="day-name">Mon</span>
            <span class="day-date">18</span>
            <span class="day-event workout">7:00am workout</span>
          </div>
          <div class="day-cell both">
            <span class="day-name">Wed</span>
            <span class="day-date">20</span>
            <span class="day-event workout">7:00am workout</span>
            <span class="day-event cook">7pm cook 1hr</span>
          </div>
          <div class="day-cell both">
            <span class="day-name">Sat</span>
            <span class="day-date">23</span>
            <span class="day-event shop">🛒 grocery</span>
            <span class="day-event cook">bulk cook 2hr</span>
          </div>
          <!-- Sun: rest (Sabbath) -->
          <div class="day-cell rest">
            <span class="day-name">Sun</span>
            <span class="day-date">24</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Saturday bulk cook -->
    <section class="card meal">
      <div class="card-header">Saturday — Bulk Cook (~2 hours)</div>
      <div class="card-body">
        <div class="recipe-grid">
          <div class="recipe-card">
            <h3><a href="../../grocery-plan/recipes/SLUG.md">Recipe Name</a></h3>
            <div class="recipe-meta">
              <span>N servings</span>
              <span class="badge meal">protein 4/5</span>
              <span>effort 2/5</span>
            </div>
          </div>
        </div>
        <h3 class="section-title" style="margin-top:1.25rem">Prep order</h3>
        <ol class="prep-steps">
          <li>Start slow cooker first (hands-off)</li>
          <li>Prep and cook second recipe while slow cooker runs</li>
        </ol>
      </div>
    </section>

    <!-- Wednesday midweek refresh -->
    <section class="card meal">
      <div class="card-header">Wednesday — Midweek Refresh (~1 hour)</div>
      <div class="card-body">
        <div class="recipe-grid"><!-- recipe cards --></div>
      </div>
    </section>

    <!-- Grocery checklist -->
    <section class="card">
      <div class="card-header">Grocery Run — Saturday Morning</div>
      <div class="card-body">
        <div class="checklist-section">
          <h3>Produce</h3>
          <ul class="checklist">
            <li>
              <input type="checkbox" id="item-1">
              <label for="item-1">
                Item
                <span class="item-note">for: Recipe Name</span>
              </label>
            </li>
          </ul>
        </div>
        <!-- repeat sections: Meat & Seafood, Dairy, Dry Goods, etc. -->
      </div>
    </section>
  </main>
</body>
</html>
```
