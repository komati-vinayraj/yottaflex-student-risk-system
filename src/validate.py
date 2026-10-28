
"""Validate generated CSV files and their relationships."""

from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/generated")


def validate_dataset(data_dir=DATA_DIR):
    data_dir = Path(data_dir)

    required_files = [
        "students.csv",
        "courses.csv",
        "enrollments.csv",
        "attendance_events.csv",
        "assessments.csv",
        "assessment_results.csv",
        "lms_activity.csv",
    ]

    for filename in required_files:
        if not (data_dir / filename).exists():
            raise FileNotFoundError(f"Missing file: {filename}")

    tables = {
        filename.removesuffix(".csv"): pd.read_csv(data_dir / filename)
        for filename in required_files
    }

    errors = []

    def check_unique(table_name, column):
        values = tables[table_name][column]
        if values.isna().any():
            errors.append(f"{table_name}.{column} contains missing IDs.")
        if values.duplicated().any():
            errors.append(f"{table_name}.{column} contains duplicate IDs.")

    def check_foreign_key(child, column, parent, parent_column):
        child_values = set(tables[child][column].dropna())
        parent_values = set(tables[parent][parent_column].dropna())
        missing = child_values - parent_values
        if missing:
            errors.append(
                f"{child}.{column} has {len(missing)} invalid references "
                f"to {parent}."
            )

    # Primary-key checks
    primary_keys = {
        "students": "student_id",
        "courses": "course_id",
        "enrollments": "enrollment_id",
        "attendance_events": "attendance_id",
        "assessments": "assessment_id",
        "assessment_results": "result_id",
        "lms_activity": "activity_id",
    }

    for table_name, column in primary_keys.items():
        check_unique(table_name, column)

    # Foreign-key checks
    check_foreign_key("enrollments", "student_id", "students", "student_id")
    check_foreign_key("enrollments", "course_id", "courses", "course_id")
    check_foreign_key(
        "attendance_events", "enrollment_id",
        "enrollments", "enrollment_id"
    )
    check_foreign_key("assessments", "course_id", "courses", "course_id")
    check_foreign_key(
        "assessment_results", "enrollment_id",
        "enrollments", "enrollment_id"
    )
    check_foreign_key(
        "assessment_results", "assessment_id",
        "assessments", "assessment_id"
    )
    check_foreign_key(
        "lms_activity", "enrollment_id",
        "enrollments", "enrollment_id"
    )

    # Allowed values and score checks
    valid_attendance = {"present", "absent", "approved_absence"}
    actual_attendance = set(
        tables["attendance_events"]["attendance_status"].dropna()
    )
    if not actual_attendance.issubset(valid_attendance):
        errors.append("Attendance contains an invalid status.")

    valid_student_status = {"active", "withdrawn", "completed"}
    actual_student_status = set(tables["students"]["status"].dropna())
    if not actual_student_status.issubset(valid_student_status):
        errors.append("Students contain an invalid status.")

    results = tables["assessment_results"]
    if not results["score"].between(0, results["max_score"]).all():
        errors.append("Assessment scores are outside the allowed range.")

    if results["score"].isna().any():
        errors.append("Assessment results contain missing scores.")

    # Verify that an assessment belongs to the enrollment's course.
    enrollment_courses = tables["enrollments"].set_index(
        "enrollment_id"
    )["course_id"]
    assessment_courses = tables["assessments"].set_index(
        "assessment_id"
    )["course_id"]

    for row in results.itertuples(index=False):
        enrollment_course = enrollment_courses.get(row.enrollment_id)
        assessment_course = assessment_courses.get(row.assessment_id)
        if enrollment_course != assessment_course:
            errors.append(
                f"Result {row.result_id} links an enrollment to an "
                "assessment from a different course."
            )
            break
    # Required-field checks
    required_columns = {
        "students": [
            "student_id", "status", "created_date",
        ],
        "courses": [
            "course_id", "course_name", "start_date", "end_date",
        ],
        "enrollments": [
            "enrollment_id", "student_id", "course_id",
            "enrollment_date", "status",
        ],
        "attendance_events": [
            "attendance_id", "enrollment_id",
            "event_date", "attendance_status",
        ],
        "assessments": [
            "assessment_id", "course_id", "assessment_date", "max_score",
        ],
        "assessment_results": [
            "result_id", "enrollment_id", "assessment_id",
            "score", "max_score", "result_status",
        ],
        "lms_activity": [
            "activity_id", "enrollment_id",
            "activity_timestamp", "activity_type",
        ],
    }

    for table_name, columns in required_columns.items():
        for column in columns:
            if column not in tables[table_name].columns:
                errors.append(
                    f"{table_name} is missing required column '{column}'."
                )
            elif tables[table_name][column].isna().any():
                errors.append(
                    f"{table_name}.{column} contains missing required values."
                )

    # Positive maximum scores
    if (results["max_score"].dropna() <= 0).any():
        errors.append("Assessment maximum scores must be positive.")

    # Validate score and maximum-score numeric values
    for column in ["score", "max_score"]:
        numeric_values = pd.to_numeric(results[column], errors="coerce")
        if numeric_values.isna().any():
            errors.append(
                f"Assessment results contain invalid numeric values in {column}."
            )

    # Check course and assessment date ordering
    courses = tables["courses"].copy()
    courses["start_date"] = pd.to_datetime(
        courses["start_date"], errors="coerce"
    )
    courses["end_date"] = pd.to_datetime(
        courses["end_date"], errors="coerce"
    )

    if courses[["start_date", "end_date"]].isna().any().any():
        errors.append("Courses contain invalid or missing dates.")
    elif (courses["end_date"] < courses["start_date"]).any():
        errors.append("A course ends before it starts.")

    assessments = tables["assessments"].copy()
    assessments["assessment_date"] = pd.to_datetime(
        assessments["assessment_date"], errors="coerce"
    )
    if assessments["assessment_date"].isna().any():
        errors.append("Assessments contain invalid or missing dates.")

    # Prevent duplicate attendance records for the same enrollment and date
    attendance = tables["attendance_events"]
    if attendance.duplicated(
        subset=["enrollment_id", "event_date"]
    ).any():
        errors.append(
            "Duplicate attendance records exist for an enrollment and date."
        )

    # Detect duplicate assessment results for the same enrollment/assessment
    if results.duplicated(
        subset=["enrollment_id", "assessment_id"]
    ).any():
        errors.append(
            "Duplicate results exist for an enrollment and assessment."
        )

    # Check enrollment and assessment date ordering
    enrollments = tables["enrollments"].copy()
    enrollments["enrollment_date"] = pd.to_datetime(
        enrollments["enrollment_date"], errors="coerce"
    )

    if enrollments["enrollment_date"].isna().any():
        errors.append("Enrollments contain invalid or missing dates.")

    valid_enrollments = enrollments[
        enrollments["enrollment_date"].notna()
    ].set_index("enrollment_id")["enrollment_date"]

    valid_assessments = assessments[
        assessments["assessment_date"].notna()
    ].set_index("assessment_id")["assessment_date"]

    for row in results.itertuples(index=False):
        enrollment_date = valid_enrollments.get(row.enrollment_id)
        assessment_date = valid_assessments.get(row.assessment_id)

        if (
            enrollment_date is not None
            and assessment_date is not None
            and assessment_date < enrollment_date
        ):
            errors.append(
                f"Result {row.result_id} refers to an assessment "
                "dated before enrollment."
            )
            break
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return False

    print("VALIDATION PASSED")
    for table_name, table in tables.items():
        print(f"{table_name}: {len(table)} rows checked")

    return True


if __name__ == "__main__":
    if not validate_dataset():
        raise SystemExit(1)
