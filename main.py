from pawpal_system import Owner, Pet, Walk, Feeding, Medication, Enrichment, Grooming, PetCareScheduler

# ── Create Owner ──────────────────────────────────────────────────────────────
owner = Owner(name="Alex", time_available=120)

# ── Create Pets ───────────────────────────────────────────────────────────────
dog = Pet(name="Buddy", species="Dog")
cat = Pet(name="Luna", species="Cat")

# ── Add Tasks OUT OF ORDER (with intentional conflict at 08:00) ───────────────
dog.add_task(Medication(description="Flea tablet",   time="09:00", frequency="weekly", priority=3, duration=5))
dog.add_task(Walk(      description="Morning walk",  time="07:00", frequency="daily",  priority=1, duration=30))
dog.add_task(Feeding(   description="Dry kibble",    time="08:00", frequency="daily",  priority=2, duration=10))

cat.add_task(Grooming(  description="Brush coat",    time="18:00", frequency="weekly", priority=4, duration=15))
cat.add_task(Enrichment(description="Laser pointer", time="19:00", frequency="daily",  priority=5, duration=10))
cat.add_task(Feeding(   description="Wet food",      time="08:00", frequency="daily",  priority=2, duration=5))

owner.add_pet(dog)
owner.add_pet(cat)

all_tasks = owner.get_all_tasks()
scheduler = PetCareScheduler(owner)

# ── Test 1: Raw (unsorted) ────────────────────────────────────────────────────
print("=" * 45)
print("  RAW TASKS (unsorted)")
print("=" * 45)
for t in all_tasks:
    print(f"  {t.time} | {t.__class__.__name__:<12} | {t.description}")

# ── Test 2: Sorted by time ────────────────────────────────────────────────────
print("\n" + "=" * 45)
print("  SORTED BY TIME")
print("=" * 45)
for t in scheduler.sort_by_time(all_tasks):
    print(f"  {t.time} | {t.__class__.__name__:<12} | {t.description}")

# ── Test 3: Filter by pet name ────────────────────────────────────────────────
print("\n" + "=" * 45)
print("  FILTER — Buddy's tasks only")
print("=" * 45)
for t in scheduler.filter_tasks(all_tasks, pet_name="Buddy"):
    print(f"  {t.time} | {t.__class__.__name__:<12} | {t.description}")

# ── Test 4: Filter by task type ───────────────────────────────────────────────
print("\n" + "=" * 45)
print("  FILTER — Feeding tasks only")
print("=" * 45)
for t in scheduler.filter_tasks(all_tasks, task_type="Feeding"):
    print(f"  {t.time} | {t.__class__.__name__:<12} | {t.description} ({t.pet.name})")

# ── Test 5: Filter by status (pending) ───────────────────────────────────────
print("\n" + "=" * 45)
print("  FILTER — Pending tasks")
print("=" * 45)
for t in scheduler.filter_tasks(all_tasks, status="pending"):
    print(f"  {t.time} | {t.__class__.__name__:<12} | {t.description}")

# ── Test 6: Combined filter (Buddy + pending) ─────────────────────────────────
print("\n" + "=" * 45)
print("  FILTER — Buddy's pending tasks, sorted")
print("=" * 45)
buddy_pending = scheduler.filter_tasks(all_tasks, pet_name="Buddy", status="pending")
for t in scheduler.sort_by_time(buddy_pending):
    print(f"  {t.time} | {t.__class__.__name__:<12} | {t.description}")

# ── Test 7: Conflict detection ────────────────────────────────────────────────
print("\n" + "=" * 45)
print("  CONFLICT DETECTION")
print("=" * 45)
conflicts = scheduler.detect_conflicts(all_tasks)
if conflicts:
    for warning in conflicts:
        print(f"  WARNING: {warning}")
else:
    print("  No conflicts found.")

print()