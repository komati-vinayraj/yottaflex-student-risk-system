
"""Generate reproducible synthetic student-risk datasets."""

from pathlib import Path
import random

import pandas as pd


DEFAULT_SEED = 20261022
START_DATE = pd.Timestamp("2025-08-01")
ATTENDANCE_START = pd.Timestamp("2025-08-04")
COURSE_END = pd.Timestamp("2026-05-31")
ASSESSMENT_DATES = [
    "2025-09-01",
    "2025-11-01",
    "2026-02-01",
    "2026-04-01",
]


def generate_dataset(
    output_dir="data/generated",
    n_students=100,
    n_courses=10,
    seed=DEFAULT_SEED,
    target_enrollments=None,
    weeks=12,
):
    """Generate synthetic CSV datasets with configurable scale."""

    if n_students < 1 or n_courses < 1 or weeks < 1:
        raise ValueError("Student, course, and week counts must be positive.")

    max_courses_per_student = min(4, n_courses)
    max_enrollments = n_students * max_courses_per_student

    if target_enrollments is not None:
        if not n_students <= target_enrollments <= max_enrollments:
            raise ValueError(
                f"target_enrollments must be between {n_students} "
                f"and {max_enrollments} for this configuration."
            )

    rng = random.Random(seed)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Students
    students = []
    for i in range(1, n_students + 1):
        students.append({
            "student_id": f"STU-2026-{i:06d}",
            "first_name": f"Student{i}",
            "age": rng.randint(18, 30),
            "status": rng.choices(
                ["active", "withdrawn", "completed"],
                weights=[85, 5, 10],
            )[0],
            "created_date": START_DATE.date().isoformat(),
        })

    # 2. Courses
    courses = []
    for i in range(1, n_courses + 1):
        courses.append({
            "course_id": f"CRS-{i:06d}",
            "course_name": f"Course {i}",
            "start_date": START_DATE.date().isoformat(),
            "end_date": COURSE_END.date().isoformat(),
        })

    # 3. Allocate enrollments.
    # When a target is supplied, distribute it exactly while keeping
    # each student's course count between 1 and max_courses_per_student.
    if target_enrollments is None:
        course_counts = [
            rng.randint(1, max_courses_per_student)
            for _ in students
        ]
    else:
        course_counts = [1] * n_students
        remaining = target_enrollments - n_students

        while remaining:
            eligible = [
                i for i, count in enumerate(course_counts)
                if count < max_courses_per_student
            ]
            student_index = rng.choice(eligible)
            course_counts[student_index] += 1
            remaining -= 1

    enrollments = []
    enrollment_number = 1

    for student, course_count in zip(students, course_counts):
        selected_courses = rng.sample(courses, course_count)

        for course in selected_courses:
            status = (
                "withdrawn"
                if student["status"] == "withdrawn"
                else "completed"
                if student["status"] == "completed"
                else "active"
            )

            enrollments.append({
                "enrollment_id": f"ENR-{enrollment_number:07d}",
                "student_id": student["student_id"],
                "course_id": course["course_id"],
                "enrollment_date": course["start_date"],
                "status": status,
            })
            enrollment_number += 1

    # 4. Attendance events.
    attendance_events = []

    for enrollment in enrollments:
        for week in range(weeks):
            event_date = (
                ATTENDANCE_START + pd.Timedelta(days=7 * week)
            ).date().isoformat()

            attendance_events.append({
                "attendance_id": (
                    f"ATT-{enrollment['enrollment_id']}-{event_date}"
                ),
                "enrollment_id": enrollment["enrollment_id"],
                "event_date": event_date,
                "attendance_status": rng.choices(
                    ["present", "absent", "approved_absence"],
                    weights=[75, 18, 7],
                )[0],
            })

    # 5. Four assessments per course.
    assessments = []

    for course in courses:
        for number, assessment_date in enumerate(ASSESSMENT_DATES, start=1):
            assessments.append({
                "assessment_id": f"ASM-{course['course_id']}-{number:02d}",
                "course_id": course["course_id"],
                "assessment_name": f"Assessment {number}",
                "assessment_date": assessment_date,
                "max_score": 100,
            })

    # Index assessments by course for efficient result generation.
    assessments_by_course = {}
    for assessment in assessments:
        assessments_by_course.setdefault(
            assessment["course_id"], []
        ).append(assessment)

    # 6. Assessment results.
    assessment_results = []

    for enrollment in enrollments:
        for assessment in assessments_by_course[enrollment["course_id"]]:
            score = rng.randint(25, 100)

            assessment_results.append({
                "result_id": (
                    f"RES-{enrollment['enrollment_id']}-"
                    f"{assessment['assessment_id']}"
                ),
                "enrollment_id": enrollment["enrollment_id"],
                "assessment_id": assessment["assessment_id"],
                "score": score,
                "max_score": assessment["max_score"],
                "result_status": "graded",
            })

    # 7. LMS activity.
    lms_activity = []
    activity_types = [
        "login", "lesson_view", "quiz_attempt", "forum_post"
    ]

    for enrollment in enrollments:
        event_count = rng.randint(2, 7)

        for event_number in range(1, event_count + 1):
            day_offset = rng.randint(0, 250)
            activity_date = START_DATE + pd.Timedelta(days=day_offset)
            timestamp = (
                activity_date
                + pd.Timedelta(
                    hours=rng.randint(8, 22),
                    minutes=rng.randint(0, 59),
                )
            )

            lms_activity.append({
                "activity_id": (
                    f"LMS-{enrollment['enrollment_id']}-"
                    f"{event_number:03d}"
                ),
                "enrollment_id": enrollment["enrollment_id"],
                "activity_timestamp": timestamp.isoformat(),
                "activity_type": rng.choice(activity_types),
            })

    tables = {
        "students": students,
        "courses": courses,
        "enrollments": enrollments,
        "attendance_events": attendance_events,
        "assessments": assessments,
        "assessment_results": assessment_results,
        "lms_activity": lms_activity,
    }

    for table_name, records in tables.items():
        pd.DataFrame(records).to_csv(
            output_path / f"{table_name}.csv",
            index=False,
        )

    print(f"Dataset generated in: {output_path.resolve()}")
    print(f"Seed: {seed}")
    for table_name, records in tables.items():
        print(f"{table_name}: {len(records)} rows")

    return tables


if __name__ == "__main__":
    generate_dataset()
