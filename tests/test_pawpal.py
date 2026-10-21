from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    task = Task(
        name="Morning walk",
        description="30 min around the block",
        duration_minutes=30,
        priority="high",
        category="walk",
    )
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_to_pet_increases_task_count():
    pet = Pet(name="Toby", species="dog", age=20)
    task = Task(
        name="Feed breakfast",
        description="Dry food",
        duration_minutes=10,
        priority="medium",
        category="feeding",
    )
    assert len(pet.tasks) == 0

    pet.add_task(task)

    assert len(pet.tasks) == 1
