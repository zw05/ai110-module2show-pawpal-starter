# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

    I wanted to add these attributes:
    A user class storing:
        - basic owner info
        - pet(s)
    A pet class storing:
        - pet info
        - tasks

    A tasks class storing:
        - the task name
        - task description
        - duration
        - priority level
    A scheduler:
        - tasks
        - time start and end
        - description

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
    - Yes, some changes that the AI suggested was a daily plan class that layouts the plan for the entire day, skipped tasks and a preferences class. I made these changes to adjust for certain edge cases like deleted tasks. 
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
    - the constraints that my scheduler consideres is priority first, and
    then time.
    - For me, priority goes over anything because it is the first thing that needs to be done and then looking at the time.
**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
    - it gives up preferences all together because thats only what the user/owner likes to do. I always think of the importance of the tasks first.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

    - Design brainstorming - I added a context.md file for the ai to read and I added the behavior and some core requirements that I put. I also asked it to suggest some other features. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
    - When it added some additional classes such as priority which I really didnt see was needed. 
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
