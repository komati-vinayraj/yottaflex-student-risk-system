# Data Dictionary

## 1. Purpose

This document describes the synthetic datasets used by the Student Risk Identification and Intervention System. Dates use ISO format (`YYYY-MM-DD`), and generated identifiers should be treated as stable keys.

## 2. Source entities

### students.csv

| Field | Type | Required | Description |
|---|---|---|---|
| student_id | String | Yes | Primary key; generated as `STU-2026-000001` |
| first_name | String | Yes | Synthetic student label; not a real person's name |
| age | Integer | Yes | Synthetic age in the range 18–30 |
| status | String | Yes | Student lifecycle status: active, withdrawn, completed |
| created_date | Date | Yes | Date the synthetic student record was created |

### courses.csv

| Field | Type | Required | Description |
|---|---|---|---|
| course_id | String | Yes | Primary key; generated as `CRS-000001` |
| course_name | String | Yes | Synthetic course name |
| start_date | Date | Yes | Course start date |
| end_date | Date | Yes | Course end date; should not precede start_date |

### enrollments.csv

| Field | Type | Required | Description |
|---|---|---|---|
| enrollment_id | String | Yes | Primary key for a student-course enrollment |
| student_id | String | Yes | Foreign key to students.student_id |
| course_id | String | Yes | Foreign key to courses.course_id |
| enrollment_date | Date | Yes | Date of enrollment |
| status | String | Yes | Enrollment lifecycle status: active, withdrawn, completed |

A student may enroll in multiple courses, and a course may contain multiple students. Each enrollment connects one student to one course.

### attendance_events.csv

| Field | Type | Required | Description |
|---|---|---|---|
| attendance_id | String | Yes | Primary key for an attendance event |
| enrollment_id | String | Yes | Foreign key to enrollments.enrollment_id |
| event_date | Date | Yes | Date of the attendance event |
| attendance_status | String | Yes | present, absent, or approved_absence |

Approved absences are excluded from the denominator used to calculate the current attendance-risk percentage. Duplicate events for the same enrollment and date should be rejected or flagged.

### assessments.csv

| Field | Type | Required | Description |
|---|---|---|---|
| assessment_id | String | Yes | Primary key for an assessment |
| course_id | String | Yes | Foreign key to courses.course_id |
| assessment_name | String | Yes | Assessment label |
| assessment_date | Date | Yes | Scheduled or recorded assessment date |
| max_score | Numeric | Yes | Maximum possible assessment score; must be positive |

### assessment_results.csv

| Field | Type | Required | Description |
|---|---|---|---|
| result_id | String | Yes | Primary key for an assessment result |
| enrollment_id | String | Yes | Foreign key to enrollments.enrollment_id |
| assessment_id | String | Yes | Foreign key to assessments.assessment_id |
| score | Numeric | Yes | Recorded score; must be between zero and max_score |
| max_score | Numeric | Yes | Maximum score used for percentage calculation |
| result_status | String | Yes | Current generator uses graded |

The assessment's course must match the course associated with the enrollment. The duplicated max_score should agree with the assessment definition.

### lms_activity.csv

| Field | Type | Required | Description |
|---|---|---|---|
| activity_id | String | Yes | Primary key for an LMS activity event |
| enrollment_id | String | Yes | Foreign key to enrollments.enrollment_id |
| activity_timestamp | Timestamp | Yes | Date and time the activity occurred |
| activity_type | String | Yes | login, lesson_view, quiz_attempt, or forum_post |

## 3. Derived output datasets

### risk_scores.csv

The risk engine generates one risk record per eligible enrollment for the selected scoring date.

| Field | Description |
|---|---|
| enrollment_id | Enrollment being scored |
| attendance_risk | Attendance-related risk component, from 0 to 100 |
| assessment_risk | Assessment-related risk component, from 0 to 100 |
| engagement_risk | LMS engagement-related risk component, from 0 to 100 |
| risk_score | Combined risk score, from 0 to 100 |
| risk_level | low, medium, high, or insufficient_data if supported by the calculation |
| explanation | Human-readable reasons supporting the score |
| as_of_date | Cutoff date used for scoring |
| rule_version | Version identifier for the scoring rules |

Risk is a rule-based indicator, not a validated probability that a student will fail.

### support_cases.csv

| Field | Description |
|---|---|
| support_case_id | Unique support case identifier |
| student_id | Student associated with the case |
| enrollment_id | Enrollment associated with the case |
| course_id | Related course |
| opened_date | Date the case was opened |
| case_type | Reason for opening the case |
| severity | Risk level used to prioritize the case |
| status | Current case status |
| source | System or process that created the case |
| description | Brief explanation of the case |

### interventions.csv

| Field | Description |
|---|---|
| intervention_id | Unique intervention identifier |
| support_case_id | Related support case |
| student_id | Student receiving the proposed intervention |
| enrollment_id | Related enrollment |
| trigger_date | Date the risk signal triggered the plan |
| intervention_date | Planned or recorded intervention date, according to status |
| type | Proposed support action |
| priority | Urgency of the proposed action |
| status | Current intervention lifecycle status |
| trigger_score | Risk score that triggered the plan |
| trigger_level | Risk category at the trigger |
| rule_version | Risk rule version that produced the trigger |
| rationale | Explanation for the proposed action |

The current implementation creates planned interventions. Planned actions should not be described as completed interventions.

## 4. Identifier and relationship rules

- Primary keys must be unique and non-null.
- Foreign keys must reference existing parent records.
- Identifiers should remain stable once assigned.
- Event timestamps must be checked against the scoring cutoff before features are calculated.
- Risk scores must be traceable to the enrollment, scoring date, and rule version.
- Ground-truth labels used for testing must not be used as model input features.

## 5. Known limitations

This dictionary describes the current prototype, not a fully normalized production database. The current generator does not yet represent every requested business entity, such as a separate intervention-outcome history. The current implementation and validation rules should be checked before treating this document as a complete production schema.
