# Design Decisions

## 1. Project architecture

The prototype separates synthetic data generation, validation, risk scoring, and intervention planning into independent Python modules. This separation makes the system easier to test, debug, and extend.

- `generator.py`: creates synthetic source datasets.
- `validate.py`: checks data quality and relationships.
- `risk_engine.py`: calculates explainable risk scores.
- `interventions.py`: creates traceable support cases and intervention plans.
- `tests/test_project.py`: checks core behavior and regression cases.

## 2. Synthetic data

Synthetic data allows development and testing without exposing real student information. A fixed random seed makes generated datasets reproducible, which supports debugging and repeatable evaluation.

The current generator is a prototype. Its scale and coverage must be expanded and verified against the final challenge requirements before claiming full-scale readiness.

## 3. Explainable rule-based scoring

The current risk engine combines three risk components:

| Component | Initial weight |
|---|---:|
| Attendance risk | 35% |
| Assessment risk | 35% |
| LMS engagement risk | 30% |

These are initial engineering choices, not weights learned from validated student outcomes. A real deployment should calibrate the weights and thresholds using appropriate historical data and expert review.

Each component is represented on a 0–100 risk scale. The engine records component scores, a combined score, a risk category, an explanation, a scoring date, and a rule version.

## 4. Historical cutoff and leakage prevention

Risk scoring uses an explicit `as_of_date`. Only source events available on or before that cutoff should influence the score. Information recorded later must not change a historical score.

A regression test modifies future attendance, assessment results, and LMS activity and verifies that scores at the earlier cutoff remain unchanged.

This matters because using future information would make evaluation misleading and could not be replicated at the time an actual intervention decision was made.

## 5. Attendance treatment

Approved absences are excluded from the current attendance-risk denominator. They should not be treated as unexcused absences.

Attendance risk is based on recorded present and absent events available by the scoring cutoff. If evidence is missing or insufficient, the system should avoid treating missing records as proof of poor attendance. Further explicit missing-data tests and behavior may still be required.

## 6. Student lifecycle

Withdrawn students and their enrollments are excluded from the active risk-scoring workflow. This prevents the system from creating new active academic-risk alerts for students who are no longer enrolled.

The lifecycle status of the student and enrollment should remain consistent and be validated when records are created or changed.

## 7. Intervention traceability

A support case and proposed intervention are linked to the relevant student and enrollment. The plan records the trigger date, score, risk category, rule version, and rationale.

The current implementation creates planned actions; it does not prove that the actions were carried out or improved academic outcomes. A fuller system should preserve intervention history and record outcomes separately.

## 8. Validation strategy

Validation checks primary-key uniqueness, foreign-key integrity, required fields, allowed status values, score ranges, and selected date and relationship constraints.

Automated tests cover reproducible generation, valid risk scores, intervention traceability, invalid references, duplicate student identifiers, future-data leakage, approved absences, and withdrawn-student exclusion.

Further work should cover lifecycle transitions, missing data, duplicate events, invalid intervention chronology, and larger-scale generation.

## 9. Human oversight and responsible use

The risk score is a support signal, not a definitive judgment about a student. Academic staff should review the underlying factors and context before taking action.

A production deployment would require access controls, privacy safeguards, fairness assessment, monitoring, and evaluation of whether interventions actually help students.
