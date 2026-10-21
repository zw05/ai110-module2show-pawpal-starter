from datetime import time

from pawpal_system import Owner, Pet, Preferences, Scheduler, Task


if __name__ == "__main__":
    #owner
    owner = Owner(
            name="Alex",
            preferences=Preferences(day_start=time(8, 0), day_end=time(18, 0)),
        )
    #pets
    buddy = Pet(name="Buddy", species="dog", age=4)
    whiskers = Pet(name="Whiskers", species="cat", age=2)
    
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    #tasks
    walk_buddy = Task(name="Walk Buddy", description="walking buddy", 
                      priority="low", category="exercise", duration_minutes=30)
    
    feed_whiskers = Task(name="Feed Whiskers", description="feeding whiskers", priority="medium", 
                         category="feeding", duration_minutes=15)

    buddy.add_task(walk_buddy)
    whiskers.add_task(feed_whiskers)


    plan = Scheduler(owner).generate_plan()
    print()
    print(plan.summary())
