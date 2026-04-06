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


### Smarter Scheduling

PawPal+ goes beyond a basic task list — the PetCareScheduler class includes
three algorithmic features that make daily pet care planning more intelligent and reliable.
Sort by time
Tasks can be added in any order and will always be displayed chronologically.
The scheduler uses Python's sorted() with a lambda key on each task's "HH:MM"
time string, so zero-padded 24-hour times sort correctly without any date parsing overhead.
Filter tasks
The filter_tasks() method runs up to three independent filter passes in sequence:

By pet name — show only tasks belonging to a specific pet
By task type — narrow down to a single activity (e.g. all Feeding tasks)
By status — show "completed", "pending", or "overdue" tasks

The "overdue" status is derived dynamically at call time using datetime.now(),
so it never goes stale. Any combination of filters can be chained together.
Conflict detection
The detect_conflicts() method scans all scheduled tasks and warns when two or more
tasks share the same time slot — across any pet. It uses a defaultdict to group tasks
by time in a single pass and returns human-readable warning strings rather than
crashing the program, keeping the scheduler fault-tolerant.