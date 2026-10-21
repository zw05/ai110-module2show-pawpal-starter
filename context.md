# Pawpal Reference File

About This Project

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.
 
A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

# Project Scope

Do not add authentication logic, a database layer, or any features not described 
in the spec.
# Requirements: UML Diagram

A user class storing:
    - basic owner info
    - pet info

A tasks class storing:
    - the task name
    - task description
    - duration
    - priority level

- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors
