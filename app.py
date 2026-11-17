from datetime import time
from pathlib import Path

import streamlit as st
from pawpal_system import Pet, Task, Owner, Preferences, Scheduler
from rag import Retriever, load_chunks
from ai_helper import NOT_CONFIGURED, OWNER_SOURCE, ask, cited_passages, owner_context
from storage import load_owner, save_owner

st.set_page_config(page_title="PawPal+", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(
    """
<style>
.block-container {padding-top: 2rem; max-width: 1100px;}
.hero {
    background: linear-gradient(135deg, #ff9a5a 0%, #ff6b8b 100%);
    border-radius: 16px; padding: 1.5rem 1.75rem; margin-bottom: 1.25rem; color: white;
}
.hero h1 {margin: 0; font-size: 2.2rem; color: white;}
.hero p {margin: .25rem 0 0; opacity: .95;}
.pet-chip {
    display: inline-block; padding: .3rem .8rem; margin: 0 .4rem .4rem 0;
    border-radius: 999px; background: #fff1e8; color: #b34a12; font-weight: 600;
    border: 1px solid #ffd2b8;
}
.badge {display:inline-block; padding:.1rem .6rem; border-radius:999px; font-size:.8rem; font-weight:600;}
.badge-high {background:#ffe0e0; color:#b00020;}
.badge-medium {background:#fff3cd; color:#8a6100;}
.badge-low {background:#e0f2e9; color:#1b6b3a;}
div.stButton > button {border-radius: 10px; font-weight: 600;}
</style>
<div class="hero">
  <h1>PawPal+</h1>
  <p>Smart daily care planning for your pets.</p>
</div>
""",
    unsafe_allow_html=True,
)

# Streamlit reruns this script on every interaction, so the Owner is kept in
# st.session_state. session_state is lost on a browser reload, so the Owner is
# also saved to disk (see storage.py) and restored here for a new session.
if "owner" not in st.session_state:
    st.session_state.owner = load_owner() or Owner(
        name="Jordan",
        preferences=Preferences(day_start=time(8, 0), day_end=time(18, 0)),
    )
owner = st.session_state.owner

PAGE_NAMES = ["Dashboard", "Pets", "Tasks", "Schedule", "Ask PawPal"]
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


@st.cache_resource
def get_retriever():
    return Retriever(load_chunks(Path(__file__).parent / "knowledge"))


def page_dashboard():
    all_tasks = owner.get_all_tasks()
    plan = Scheduler(owner).generate_plan() if all_tasks else None
    high = sum(1 for _, t in all_tasks if t.priority == "high")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pets", len(owner.pets))
    m2.metric("Tasks", len(all_tasks))
    m3.metric("High priority", high)
    m4.metric("Scheduled minutes", plan.total_minutes() if plan else 0)

    left, right = st.columns([3, 2])
    with left:
        st.markdown("### Today's schedule")
        if plan and plan.scheduled:
            st.dataframe(
                width="stretch",
                hide_index=True,
                data=[
                    {
                        "time": f"{i.start_time:%H:%M}-{i.end_time:%H:%M}",
                        "pet": i.pet.name,
                        "task": i.task.name,
                        "priority": i.task.priority,
                    }
                    for i in plan.scheduled
                ],
            )
            if plan.skipped:
                st.warning(f"{len(plan.skipped)} task(s) did not fit in the day. See the Schedule page.")
        else:
            st.info("Nothing scheduled yet. Add pets and tasks to get started.")
    with right:
        st.markdown("### Pets")
        if owner.pets:
            st.dataframe(
                width="stretch",
                hide_index=True,
                data=[
                    {"name": p.name, "species": p.species, "age": p.age, "tasks": len(p.tasks)}
                    for p in owner.pets
                ],
            )
        else:
            st.info("No pets yet.")


def page_pets():
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
        st.markdown(
            "".join(f'<span class="pet-chip">{p.name} - {p.age}y</span>' for p in owner.pets),
            unsafe_allow_html=True,
        )
    else:
        st.info("No pets yet. Add one above.")


def page_tasks():
    st.markdown("### Tasks")
    if not owner.pets:
        st.info("Add a pet on the Pets page before adding tasks.")
        return

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
        st.dataframe(
            width="stretch",
            hide_index=True,
            data=[
                {
                    "pet": pet.name,
                    "task": task.name,
                    "minutes": task.duration_minutes,
                    "priority": task.priority,
                    "category": task.category,
                }
                for pet, task in all_tasks
            ],
        )
    else:
        st.info("No tasks yet. Add one above.")


def page_schedule():
    st.markdown("### Schedule")
    if st.button("Generate schedule"):
        plan = Scheduler(owner).generate_plan()
        if plan.scheduled or plan.skipped:
            m1, m2, m3 = st.columns(3)
            m1.metric("Scheduled", len(plan.scheduled))
            m2.metric("Skipped", len(plan.skipped))
            m3.metric("Total minutes", plan.total_minutes())
            for item in plan.scheduled:
                p = item.task.priority
                st.markdown(
                    f"**{item.start_time:%H:%M}-{item.end_time:%H:%M}** &nbsp; "
                    f"{item.pet.name}: {item.task.name} "
                    f'<span class="badge badge-{p}">{p}</span>',
                    unsafe_allow_html=True,
                )
                st.caption(item.reason)
            if plan.skipped:
                with st.expander(f"Skipped tasks ({len(plan.skipped)})"):
                    for item in plan.skipped:
                        st.markdown(f"**{item.pet.name}: {item.task.name}**")
                        st.caption(item.reason)
        else:
            st.warning("Nothing to schedule. Add a pet and some tasks first.")


def page_ask():
    st.markdown("### Ask PawPal")
    st.caption("Pet-care questions answered from our care guides. General guidance, not veterinary advice.")

    ask_pet = None
    if owner.pets:
        ask_index = st.selectbox(
            "About which pet?",
            options=[None] + list(range(len(owner.pets))),
            format_func=lambda i: "Any pet" if i is None else owner.pets[i].name,
            key="ask_pet",
        )
        if ask_index is not None:
            ask_pet = owner.pets[ask_index]

    question = st.text_input("Your question", placeholder="How much exercise does a senior dog need?")
    if st.button("Ask") and question.strip():
        with st.spinner("Looking through the care guides..."):
            answer, hits = ask(question, get_retriever(), pet=ask_pet, owner=owner)
        if answer == NOT_CONFIGURED:
            st.info(NOT_CONFIGURED + " Showing the most relevant guide passages instead.")
            if not hits:
                st.write("I don't have guidance on that yet.")
        else:
            st.write(answer)
        # Without AI there is no answer to cite, so show the best-matching guides.
        # With AI, show only the sources the answer actually cites.
        if answer == NOT_CONFIGURED:
            shown = hits
        else:
            shown = cited_passages(answer, hits, owner_context(owner))
        if shown:
            with st.expander("Sources", expanded=answer == NOT_CONFIGURED):
                for chunk, score in shown:
                    label = "Your PawPal data" if chunk.source == OWNER_SOURCE else chunk.source
                    suffix = f" (score {score:.1f})" if score is not None else ""
                    st.markdown(f"**{label}** - {chunk.heading}{suffix}")
                    st.text(chunk.text)


PAGES = {
    "Dashboard": page_dashboard,
    "Pets": page_pets,
    "Tasks": page_tasks,
    "Schedule": page_schedule,
    "Ask PawPal": page_ask,
}

with st.sidebar:
    st.markdown("### Navigation")
    owner.name = st.text_input("Owner name", value=owner.name)
    for name in PAGE_NAMES:
        st.button(
            name,
            key=f"nav_{name}",
            width="stretch",
            type="primary" if st.session_state.page == name else "secondary",
            on_click=st.session_state.__setitem__,
            args=("page", name),
        )

PAGES[st.session_state.page]()

# Persist after every run so a reload or restart keeps pets and tasks.
save_owner(owner)
