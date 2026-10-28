
"""Automated tests for the student risk system."""
from src.interventions import generate_interventions
import pandas as pd

from src.generator import generate_dataset
from src.validate import validate_dataset
from src.risk_engine import calculate_risk


def test_generated_dataset_passes_validation(tmp_path):
    """Generated tables should have valid IDs and relationships."""
    generate_dataset(
        output_dir=tmp_path,
        n_students=20,
        n_courses=5,
        seed=123,
    )

    assert validate_dataset(tmp_path) is True


def test_generator_is_reproducible(tmp_path):
    """The same seed should produce identical source CSV files."""
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    generate_dataset(first_dir, n_students=20, n_courses=5, seed=456)
    generate_dataset(second_dir, n_students=20, n_courses=5, seed=456)

    source_files = [
        "students.csv",
        "courses.csv",
        "enrollments.csv",
        "attendance_events.csv",
        "assessments.csv",
        "assessment_results.csv",
        "lms_activity.csv",
    ]

    for filename in source_files:
        assert (
            (first_dir / filename).read_bytes()
            == (second_dir / filename).read_bytes()
        )


def test_risk_scores_are_valid(tmp_path):
    """Risk scores should be bounded and active enrollments only."""
    generate_dataset(
        output_dir=tmp_path,
        n_students=30,
        n_courses=5,
        seed=789,
    )

    scores = calculate_risk(
        data_dir=tmp_path,
        as_of_date="2025-10-15",
    )

    students = pd.read_csv(tmp_path / "students.csv")
    enrollments = pd.read_csv(tmp_path / "enrollments.csv")

    active_student_ids = set(
        students.loc[students["status"] == "active", "student_id"]
    )
    expected = enrollments[
        (enrollments["status"] == "active")
        & (enrollments["student_id"].isin(active_student_ids))
    ]

    assert len(scores) == len(expected)
    assert scores["enrollment_id"].is_unique
    assert scores["risk_level"].isin(
        ["low", "medium", "high", "insufficient_data"]
    ).all()

    scored = scores["risk_score"].dropna()
    assert scored.between(0, 100).all()

    # Each scoring decision must record its cutoff and rule version.
    assert (scores["as_of_date"] == "2025-10-15").all()
    assert (scores["rule_version"] == "v1").all()
def test_interventions_are_traceable(tmp_path):
    from src.generator import generate_dataset
    from src.risk_engine import calculate_risk

    generate_dataset(
        output_dir=tmp_path,
        n_students=20,
        n_courses=5,
        seed=123,
    )

    calculate_risk(
        data_dir=tmp_path,
        as_of_date="2025-10-15",
    )

    cases, interventions = generate_interventions(data_dir=tmp_path)

    assert len(cases) == len(interventions)

    case_ids = {case["support_case_id"] for case in cases}
    assert len(case_ids) == len(cases)

    for intervention in interventions:
        assert intervention["support_case_id"] in case_ids
        assert intervention["status"] == "planned"
        assert intervention["trigger_date"] == intervention["intervention_date"]
        assert intervention["rule_version"]
        assert 0 <= intervention["trigger_score"] <= 100
def test_validator_rejects_duplicate_student_id(tmp_path):
    import pandas as pd
    from src.generator import generate_dataset
    from src.validate import validate_dataset

    generate_dataset(
        output_dir=tmp_path,
        n_students=10,
        n_courses=3,
        seed=123,
    )

    path = tmp_path / "students.csv"
    students = pd.read_csv(path)

    # Deliberately duplicate a primary key.
    students = pd.concat([students, students.iloc[[0]]], ignore_index=True)
    students.to_csv(path, index=False)

    assert validate_dataset(tmp_path) is False


def test_validator_rejects_invalid_student_reference(tmp_path):
    import pandas as pd
    from src.generator import generate_dataset
    from src.validate import validate_dataset

    generate_dataset(
        output_dir=tmp_path,
        n_students=10,
        n_courses=3,
        seed=123,
    )

    path = tmp_path / "enrollments.csv"
    enrollments = pd.read_csv(path)

    # Deliberately reference a student that does not exist.
    enrollments.loc[0, "student_id"] = "STU-9999-999999"
    enrollments.to_csv(path, index=False)

    assert validate_dataset(tmp_path) is False
def test_future_records_do_not_change_past_risk_scores(tmp_path):
    import pandas as pd
    from src.generator import generate_dataset
    from src.risk_engine import calculate_risk

    cutoff = "2025-08-10"

    generate_dataset(
        output_dir=tmp_path,
        n_students=20,
        n_courses=5,
        seed=123,
    )

    # Calculate risk using only information available at the cutoff.
    calculate_risk(data_dir=tmp_path, as_of_date=cutoff)
    original = pd.read_csv(tmp_path / "risk_scores.csv")

    # Make future attendance records look worse.
    attendance_path = tmp_path / "attendance_events.csv"
    attendance = pd.read_csv(attendance_path)
    future_attendance = attendance["event_date"] > cutoff
    attendance.loc[future_attendance, "attendance_status"] = "absent"
    attendance.to_csv(attendance_path, index=False)

    # Make future assessment scores very low.
    assessments = pd.read_csv(tmp_path / "assessments.csv")
    future_assessment_ids = set(
        assessments.loc[
            assessments["assessment_date"] > cutoff, "assessment_id"
        ]
    )

    results_path = tmp_path / "assessment_results.csv"
    results = pd.read_csv(results_path)
    future_results = results["assessment_id"].isin(future_assessment_ids)
    results.loc[future_results, "score"] = 0
    results.to_csv(results_path, index=False)

    # Move future LMS activities further into the future.
    lms_path = tmp_path / "lms_activity.csv"
    lms = pd.read_csv(lms_path)
    future_lms = pd.to_datetime(
        lms["activity_timestamp"], errors="coerce"
    ) > pd.Timestamp(cutoff)
    lms.loc[future_lms, "activity_timestamp"] = "2026-12-01T12:00:00"
    lms.to_csv(lms_path, index=False)

    # Recalculate using the same cutoff.
    calculate_risk(data_dir=tmp_path, as_of_date=cutoff)
    changed = pd.read_csv(tmp_path / "risk_scores.csv")

    columns = [
        "enrollment_id",
        "attendance_risk",
        "assessment_risk",
        "engagement_risk",
        "risk_score",
        "risk_level",
    ]

    pd.testing.assert_frame_equal(
        original[columns].sort_values("enrollment_id").reset_index(drop=True),
        changed[columns].sort_values("enrollment_id").reset_index(drop=True),
    )

def test_approved_absences_do_not_change_attendance_risk(tmp_path):
    import pandas as pd
    from src.generator import generate_dataset
    from src.risk_engine import calculate_risk

    cutoff = "2025-08-10"

    generate_dataset(
        output_dir=tmp_path,
        n_students=10,
        n_courses=3,
        seed=123,
    )

    # Calculate the original attendance risk.
    calculate_risk(data_dir=tmp_path, as_of_date=cutoff)
    original = pd.read_csv(tmp_path / "risk_scores.csv")

    enrollments = pd.read_csv(tmp_path / "enrollments.csv")
    attendance_path = tmp_path / "attendance_events.csv"
    attendance = pd.read_csv(attendance_path)

    # Add approved absences without changing existing attendance records.
    extra_absences = pd.DataFrame([
        {
            "attendance_id": f"TEST-APPROVED-{row.enrollment_id}",
            "enrollment_id": row.enrollment_id,
            "event_date": "2025-08-08",
            "attendance_status": "approved_absence",
        }
        for row in enrollments.itertuples()
    ])

    attendance = pd.concat(
        [attendance, extra_absences],
        ignore_index=True,
    )
    attendance.to_csv(attendance_path, index=False)

    # Recalculate risk after adding approved absences.
    calculate_risk(data_dir=tmp_path, as_of_date=cutoff)
    changed = pd.read_csv(tmp_path / "risk_scores.csv")

    original = original.sort_values("enrollment_id").reset_index(drop=True)
    changed = changed.sort_values("enrollment_id").reset_index(drop=True)

    pd.testing.assert_series_equal(
        original["attendance_risk"],
        changed["attendance_risk"],
        check_names=False,
    )

def test_withdrawn_students_are_excluded_from_risk_scores(tmp_path):
    import pandas as pd
    from src.generator import generate_dataset
    from src.risk_engine import calculate_risk

    generate_dataset(
        output_dir=tmp_path,
        n_students=20,
        n_courses=5,
        seed=123,
    )

    # Select one student and mark them as withdrawn.
    students_path = tmp_path / "students.csv"
    students = pd.read_csv(students_path)
    withdrawn_student_id = students.iloc[0]["student_id"]

    students.loc[
        students["student_id"] == withdrawn_student_id,
        "status",
    ] = "withdrawn"

    students.to_csv(students_path, index=False)

    # Get every enrollment belonging to this student.
    enrollments = pd.read_csv(tmp_path / "enrollments.csv")
    withdrawn_enrollment_ids = set(
        enrollments.loc[
            enrollments["student_id"] == withdrawn_student_id,
            "enrollment_id",
        ]
    )

    # Calculate risk scores.
    calculate_risk(
        data_dir=tmp_path,
        as_of_date="2025-10-15",
    )

    risk_scores = pd.read_csv(tmp_path / "risk_scores.csv")
    scored_enrollment_ids = set(risk_scores["enrollment_id"])

    # No withdrawn student's enrollment should be scored.
    assert withdrawn_enrollment_ids.isdisjoint(scored_enrollment_ids)
