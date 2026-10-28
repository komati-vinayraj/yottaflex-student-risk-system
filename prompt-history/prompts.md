
# AI Prompt History

## Purpose

This document records the AI-assisted development work used for the YottaFlex student-risk challenge. It summarizes the main development requests and technical guidance used during this project.

**Transparency note:** This is a reconstructed summary, not a verbatim transcript of every prompt and response. Any additional prompts sent to ChatGPT or other AI tools must be added before submission. Do not describe this file as a complete transcript unless it has been verified against the actual history.

## 1. Project design and requirements

**Tool:** ChatGPT

**Prompt summary:** Help plan an end-to-end synthetic student-risk system covering students, courses, enrollments, attendance, assessments, LMS activity, support cases, interventions, and outcomes. Identify appropriate data fields, relationships, validation rules, edge cases, and acceptance criteria.

**Use:** Established the project structure, data model, data-generation approach, and validation priorities.

## 2. Synthetic data generator

**Tool:** ChatGPT

**Prompt summary:** Help implement a reproducible Python generator for configurable synthetic student datasets, with a fixed random seed, CSV exports, consistent identifiers, and configurable numbers of students, courses, enrollments, and attendance weeks.

**Use:** Developed and tested the synthetic data generator.

## 3. Data validation and automated tests

**Tool:** ChatGPT

**Prompt summary:** Help validate primary-key uniqueness, foreign-key references, reproducibility, valid risk-score ranges, approved-absence handling, withdrawn-student exclusion, intervention traceability, and prevention of future-data leakage.

**Use:** Built and ran the project validation checks and automated tests.

## 4. Risk scoring

**Tool:** ChatGPT

**Prompt summary:** Help implement explainable historical risk scoring using attendance, assessment performance, and recent LMS activity. Respect a scoring cutoff date, exclude approved absences from absence calculations, handle missing signals, and produce explanations for risk classifications.

**Use:** Implemented the initial risk engine and verified its behavior with automated tests.

## 5. Performance optimization

**Tool:** ChatGPT

**Prompt summary:** Optimize the risk engine after repeated filtering of large attendance, assessment, and LMS tables caused slow execution. Preserve scoring rules and historical cutoff protections while using grouped calculations and joins.

**Use:** Reworked calculations to use Pandas groupby operations and joins. The optimized version passed all nine existing tests and processed the full dataset.

## 6. Support cases and interventions

**Tool:** ChatGPT

**Prompt summary:** Help create support cases and intervention plans from medium- and high-risk enrollments, with traceable enrollment references, trigger dates, risk scores, rule versions, priorities, and rationales.

**Use:** Implemented and tested intervention generation.

## 7. Documentation and submission preparation

**Tool:** ChatGPT

**Prompt summary:** Help prepare the README, data dictionary, design-decision documentation, validation report, Git configuration, `.gitignore`, and a safe public GitHub submission workflow.

**Use:** Prepared documentation and excluded generated datasets and local environment files from version control.

## Important limitations

- The prompts above are summaries, not guaranteed verbatim copies of the original messages.
- Record additional prompts from any other AI tools used.
- Verify that the submitted documentation matches the implemented code.
- Do not include credentials, access tokens, private data, or confidential assessment material in the public repository.
