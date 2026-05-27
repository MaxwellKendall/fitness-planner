# /adjust — Per-Week Exceptions and Adjustments

Handle schedule conflicts, injuries, time constraints, or energy constraints for the current week. Updates the affected HTML plan file in place.

## Steps

1. **Identify the constraint**
   - Which session(s) are affected?
   - What type: injury/pain · schedule conflict · time constraint · energy/recovery

2. **Injury or pain flare-up**
   - Read the affected exercise cards from `exercise-library/`
   - Remove exercises targeting the affected area (muscles_primary or muscles_secondary)
   - Find substitutes from the exercise card's `substitutes` field that avoid the area
   - Reduce volume by 20–30% if the injury affects multiple patterns
   - Add a visible alert banner to the affected session card in the HTML

3. **Schedule conflict**
   - Reschedule to the next available preferred day
   - Enforce minimum 48h between sessions targeting the same primary pattern
   - If no slot is available this week, reduce to a shorter session rather than dropping entirely

4. **Time constraint**
   - Available time < session_duration_minutes → scale proportionally
   - Prioritize: compound primary lifts → compound accessories → isolation
   - Drop isolation work first, then reduce sets on accessories, keep main lift intact
   - Update session duration in the HTML header

5. **Energy / recovery**
   - User flagged low energy or sore → reduce RPE ceiling by 1–2, drop sets by 20%
   - Never increase volume or intensity to "make up" for a prior missed session

6. **Update the plan HTML**
   - Edit `plans/YYYY-MM-DD.html` in place
   - Add a visible `<div class="alert warning">Adjusted: [reason]</div>` at the top of the affected session card
   - Mark the session card with `data-adjusted="true"` attribute

7. **Do not modify config.yaml** — ADJUST is per-week only.
   - If the same constraint recurs 3+ times → surface it in the next /review as a candidate for permanent config change.

8. **Show the user the modified section** before writing.

---

## Output format note

ADJUST edits the existing `plans/YYYY-MM-DD.html` in place. It does not create a new file. Modified sessions get an alert banner:

```html
<div class="alert warning">
  <strong>Adjusted:</strong> [reason — e.g., "right shoulder soreness — replaced bench press with push-ups, volume reduced 25%"]
</div>
```

And the session card gets a visual indicator:

```html
<section class="card workout" data-adjusted="true">
  <div class="card-header">
    Wednesday, YYYY-MM-DD — Session B
    <span class="badge recovery" style="margin-left:auto">adjusted</span>
  </div>
  ...
</section>
```
