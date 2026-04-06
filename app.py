import streamlit as st
from pawpal_system import Owner, Pet, Walk, Feeding, Medication, Enrichment, Grooming, PetCareScheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

st.divider()

# ── Session state: Owner & Pet vault ──────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None

if "pet" not in st.session_state:
    st.session_state.pet = None

if "tasks" not in st.session_state:
    st.session_state.tasks = []

# ── Step 1: Add Owner & Pet ───────────────────────────────────────────────────
st.subheader("Step 1: Set Up Owner & Pet")

owner_name = st.text_input("Owner name", value="Jordan")
time_available = st.number_input("Time available (minutes)", min_value=10, max_value=480, value=120)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add Pet"):
    # Create Owner and Pet using Phase 2 methods
    owner = Owner(name=owner_name, time_available=int(time_available))
    pet = Pet(name=pet_name, species=species)
    owner.add_pet(pet)                        # Owner.add_pet()

    st.session_state.owner = owner
    st.session_state.pet = pet
    st.session_state.tasks = []               # reset tasks for new pet
    st.success(f"✅ {pet_name} added to {owner_name}'s profile!")

if st.session_state.pet:
    st.info(f"Current pet: **{st.session_state.pet.name}** ({st.session_state.pet.species})")

st.divider()

# ── Step 2: Schedule Tasks ────────────────────────────────────────────────────
st.subheader("Step 2: Schedule a Task")
st.caption("Add tasks to your pet's schedule.")

TASK_TYPES = {
    "Walk": Walk,
    "Feeding": Feeding,
    "Medication": Medication,
    "Enrichment": Enrichment,
    "Grooming": Grooming,
}
PRIORITY_MAP = {"high": 1, "medium": 2, "low": 3}

col1, col2, col3 = st.columns(3)
with col1:
    task_type = st.selectbox("Task type", list(TASK_TYPES.keys()))
    task_title = st.text_input("Description", value="Morning walk")
with col2:
    task_time = st.text_input("Time", value="08:00 AM")
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly"])
    priority = st.selectbox("Priority", ["high", "medium", "low"])

if st.button("Add Task"):
    if st.session_state.pet is None:
        st.warning("Please add a pet first before scheduling tasks.")
    else:
        # Instantiate the correct Task subclass using Phase 2 classes
        TaskClass = TASK_TYPES[task_type]
        task = TaskClass(
            description=task_title,
            time=task_time,
            frequency=frequency,
            priority=PRIORITY_MAP[priority],
            duration=int(duration)
        )
        st.session_state.pet.add_task(task)       # Pet.add_task()
        st.session_state.tasks = st.session_state.pet.get_tasks()  # Pet.get_tasks()
        st.success(f"✅ {task_type} task '{task_title}' added!")

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table([{
        "Type": t.__class__.__name__,
        "Description": t.description,
        "Time": t.time,
        "Duration (min)": t.duration,
        "Priority": t.priority,
        "Done": "✓" if t.completed else "✗"
    } for t in st.session_state.tasks])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Step 3: Generate Schedule ─────────────────────────────────────────────────
st.subheader("Step 3: Generate Schedule")
st.caption("Runs the scheduler and displays today's plan.")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Please add at least one task before generating a schedule.")
    else:
        scheduler = PetCareScheduler(st.session_state.owner)   # PetCareScheduler
        plan = scheduler.generate_plan()                        # generate_plan()

        st.success("Schedule generated!")
        st.markdown("### Today's Schedule")
        for task in plan:
            st.markdown(
                f"- **Priority {task.priority}** | `{task.__class__.__name__}` — "
                f"{task.description} @ {task.time} ({task.duration} min)"
            )

        total = st.session_state.owner.get_total_task_time()   # Owner.get_total_task_time()
        available = st.session_state.owner.time_available
        if total > available:
            st.warning(f"⚠️ Total time needed ({total} min) exceeds available time ({available} min).")
        else:
            st.info(f"✅ Total time: {total} min / {available} min available.")