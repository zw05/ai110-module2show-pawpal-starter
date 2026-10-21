from datetime import time

import streamlit as st
from pawpal_system import Pet, Task, Owner, Preferences, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Streamlit reruns this script on every interaction, so the Owner is kept in
# st.session_state and only created the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        preferences=Preferences(day_start=time(8, 0), day_end=time(18, 0)),
    )
owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.markdown("### Pets")
col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    age = st.number_input("Age", min_value=0, max_value=40, value=1)

if st.button("Add pet"):
    owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))

if owner.pets:
    st.write("Pets:", ", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
if owner.pets:
    pet_index = st.selectbox(
        "Pet", options=range(len(owner.pets)), format_func=lambda i: owner.pets[i].name
    )
    pet_choice = owner.pets[pet_index]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        category = st.selectbox(
            "Category", ["walk", "feeding", "medication", "enrichment", "grooming", "other"]
        )

    if st.button("Add task"):
        pet_choice.add_task(
            Task(
                name=task_title,
                description="",
                duration_minutes=int(duration),
                priority=priority,
                category=category,
            )
        )

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("Current tasks:")
        st.table(
            [
                {
                    "pet": pet.name,
                    "task": task.name,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "category": task.category,
                }
                for pet, task in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.info("Add a pet before adding tasks.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    plan = Scheduler(owner).generate_plan()
    if plan.scheduled or plan.skipped:
        st.text(plan.summary())
    else:
        st.warning("Nothing to schedule. Add a pet and some tasks first.")
