# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```
Plan for 2026-10-20 (45 min scheduled)
  08:00-08:15  Whiskers: Feed Whiskers [medium] - medium priority, 15 min
  08:15-08:45  Buddy: Walk Buddy [low] - low priority, 30 min

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```
==================== test session starts =====================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\darkn\Projects\school\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 7 items                                             

tests\test_pawpal.py .......                            [100%]

===================== 7 passed in 0.05s ======================
Confidence Level - 4

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Run the app with `streamlit run app.py`.

### Main UI features

| Section | What you can do |
|---------|-----------------|
| **Owner** | Edit the owner name (the day runs 08:00-18:00 by default). |
| **Pets** | Enter a name, species (dog, cat, other) and age, then click **Add pet**. All pets are listed below the form. |
| **Tasks** | Pick a pet, enter a title, duration (1-240 min), priority (low, medium, high) and category (walk, feeding, medication, enrichment, grooming, other), then click **Add task**. A table shows every task across all pets. |
| **Build Schedule** | Click **Generate schedule** to see today's plan, with a reason for each task and a list of skipped tasks. |

### Example workflow

1. Open the app and set the owner name.
2. Add a pet, e.g. **Buddy** (dog, age 4), then add a second pet, e.g. **Whiskers** (cat, age 2).
3. With Buddy selected, add the task **Walk Buddy**: 30 min, low priority, category walk.
4. Select Whiskers and add **Feed Whiskers**: 15 min, medium priority, category feeding.
5. Click **Generate schedule** and read today's plan:

```
Plan for 2026-10-20 (45 min scheduled)
  08:00-08:15  Whiskers: Feed Whiskers [medium] - medium priority, 15 min
  08:15-08:45  Buddy: Walk Buddy [low] - low priority, 30 min
```

### Key Scheduler behaviors shown

- **Sorting:** tasks from all pets are merged and ranked by priority (high first), then shorter duration, then name. In the example above, the medium-priority feeding comes before the low-priority walk even though it was added second.
- **Back-to-back placement:** tasks are placed one after another from the start of the day, so scheduled tasks never overlap.
- **Skipping with a reason:** a task that does not fit in the remaining time (or exceeds the max task length) is listed under *Skipped* with an explanation, and later, shorter tasks can still be scheduled.
- **Completed tasks are left out** of the plan.
- **Not implemented:** conflict warnings, duplicate flagging and recurring tasks. Duplicate tasks are currently both scheduled without a warning.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
