# Student Risk Identification and Intervention System

## 1. Project overview

This project generates synthetic student data, validates data quality, calculates explainable academic risk scores, and creates traceable support cases and intervention plans.

The system uses historical attendance, assessment performance, and recent LMS activity to help identify active enrollments that may need academic support.

## 2. Technology stack

- Python 3.10
- Pandas
- NumPy
- SQLite (planned; not yet implemented)
- Pytest

## 3. Current features

- Reproducible synthetic data generation using a fixed random seed.
- CSV datasets for students, courses, enrollments, attendance, assessments, assessment results, and LMS activity.
- Data validation for primary keys, foreign keys, required fields, allowed values, and selected date and score constraints.
- Explainable risk scoring based on attendance, assessment results, and recent LMS activity.
- Risk categories: low, medium, and high.
- Risk explanations, scoring dates, and rule-version tracking.
- Support case and intervention plan generation.
- Automated tests for reproducibility, validation, risk-score integrity, intervention traceability, future-data leakage, approved absences, and withdrawn students.

## 4. Setup

Create and activate a virtual environment if you do not already have one:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## 5. Run the project

Run these commands from the project root.

Generate the default synthetic dataset:

```powershell
python -m src.generator
```

Validate the generated data:

```powershell
python -m src.validate
```

Calculate risk scores:

```powershell
python -m src.risk_engine
```

Generate support cases and intervention plans:

```powershell
python -m src.interventions
```

Run the test suite:

```powershell
python -m pytest -v
```

## 6. Output files

Generated CSV files are saved under `data/generated/`.

Expected outputs include:

- Source datasets for the entities listed above.
- `risk_scores.csv`
- `support_cases.csv`
- `interventions.csv`

The exact row counts depend on the generator configuration and generated records.

## 7. Risk scoring approach

The current rule-based model uses these initial weights:

- Attendance risk: 35%
- Assessment risk: 35%
- LMS engagement risk: 30%

The scoring logic uses information available on or before the selected scoring date. Approved absences are excluded from the attendance-risk calculation. Withdrawn students and their enrollments are excluded from active risk scoring.

Risk thresholds and weights are configurable design choices, not clinically or institutionally validated predictions. They should be calibrated with appropriate historical data before operational use.

## 8. Testing and data quality

The automated test suite checks reproducibility, core data integrity, risk-score ranges, intervention traceability, historical scoring behavior, approved absences, and withdrawn-student exclusion.

Run `python -m pytest -v` to execute the tests.

## 9. Limitations and future work

- The data is synthetic and does not demonstrate real-world predictive accuracy.
- The generator supports configurable dataset sizes. A dataset containing 5,000 students, 200 courses, and 20,000 enrollments was generated and validated during development.
- SQLite persistence, a unified application entry point, and a dashboard are not implemented.
- Additional tests are needed for missing data, temporal violations, lifecycle transitions, and other labelled edge cases.
- Intervention effectiveness has not yet been evaluated against outcomes recorded after an intervention.

## 10. Responsible use

This prototype is intended to help academic staff identify students who may benefit from support. Risk scores should not be treated as definitive judgments about students. Any real deployment requires privacy safeguards, access controls, fairness evaluation, and human oversight.