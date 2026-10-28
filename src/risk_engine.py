
"""Explainable, historical student risk scoring."""

from pathlib import Path
import pandas as pd

WEIGHTS = {
    "attendance_risk": 0.35,
    "assessment_risk": 0.35,
    "engagement_risk": 0.30,
}


def calculate_risk(data_dir="data/generated", as_of_date="2025-10-15"):
    """Score active enrollments using only information available by cutoff."""

    data_dir = Path(data_dir)
    cutoff = pd.Timestamp(as_of_date)
    window_start = cutoff - pd.Timedelta(days=30)

    students = pd.read_csv(data_dir / "students.csv")
    enrollments = pd.read_csv(data_dir / "enrollments.csv")
    attendance = pd.read_csv(data_dir / "attendance_events.csv")
    assessments = pd.read_csv(data_dir / "assessments.csv")
    results = pd.read_csv(data_dir / "assessment_results.csv")
    activity = pd.read_csv(data_dir / "lms_activity.csv")

    # Include only active students in active enrollments.
    active_students = students.loc[
        students["status"].eq("active"), "student_id"
    ]
    active_enrollments = enrollments[
        enrollments["status"].eq("active")
        & enrollments["student_id"].isin(active_students)
    ].copy()

    # 1. Calculate attendance risk once per enrollment.
    attendance["event_date"] = pd.to_datetime(
        attendance["event_date"], errors="coerce"
    )
    attendance = attendance[attendance["event_date"].le(cutoff)]

    eligible = attendance[
        attendance["attendance_status"].isin(["present", "absent"])
    ].copy()

    eligible["is_absent"] = eligible["attendance_status"].eq("absent")
    attendance_metrics = (
        eligible.groupby("enrollment_id")["is_absent"]
        .mean()
        .mul(100)
        .rename("attendance_risk")
        .reset_index()
    )

    # 2. Calculate assessment risk using results available by cutoff.
    assessments["assessment_date"] = pd.to_datetime(
        assessments["assessment_date"], errors="coerce"
    )

    dated_results = results.merge(
        assessments[["assessment_id", "assessment_date"]],
        on="assessment_id",
        how="left",
        validate="many_to_one",
    )

    dated_results = dated_results[
        dated_results["assessment_date"].le(cutoff)
        & dated_results["max_score"].gt(0)
        & dated_results["score"].notna()
    ].copy()

    dated_results["score_percentage"] = (
        dated_results["score"] / dated_results["max_score"] * 100
    )

    assessment_metrics = (
        dated_results.groupby("enrollment_id")["score_percentage"]
        .mean()
        .rsub(100)
        .rename("assessment_risk")
        .reset_index()
    )

    # 3. Count LMS activity in the preceding 30-day window.
    activity["activity_timestamp"] = pd.to_datetime(
        activity["activity_timestamp"], errors="coerce"
    )
    recent_activity = activity[
        activity["activity_timestamp"].le(cutoff)
        & activity["activity_timestamp"].ge(window_start)
    ]

    activity_metrics = (
        recent_activity.groupby("enrollment_id")
        .size()
        .rename("activity_count")
        .reset_index()
    )

    # Join precomputed metrics instead of rescanning large tables per row.
    scored = (
        active_enrollments
        .merge(attendance_metrics, on="enrollment_id", how="left")
        .merge(assessment_metrics, on="enrollment_id", how="left")
        .merge(activity_metrics, on="enrollment_id", how="left")
    )
    scored["activity_count"] = (
        scored["activity_count"].fillna(0).astype(int)
    )

    output = []

    for row in scored.itertuples(index=False):
        factors = {}
        explanations = []

        if pd.notna(row.attendance_risk):
            attendance_risk = float(row.attendance_risk)
            factors["attendance_risk"] = attendance_risk

            if attendance_risk >= 25:
                explanations.append(
                    f"High absence rate ({attendance_risk:.1f}%)"
                )

        if pd.notna(row.assessment_risk):
            assessment_risk = float(row.assessment_risk)
            factors["assessment_risk"] = assessment_risk
            average_percentage = 100 - assessment_risk

            if average_percentage < 60:
                explanations.append(
                    f"Low assessment average ({average_percentage:.1f}%)"
                )

        activity_count = int(row.activity_count)
        engagement_risk = max(
            0.0, 100.0 * (1 - activity_count / 10)
        )
        factors["engagement_risk"] = engagement_risk

        if activity_count < 3:
            explanations.append(
                f"Low LMS activity ({activity_count} events in 30 days)"
            )

        available_weight = sum(WEIGHTS[name] for name in factors)

        if available_weight == 0:
            risk_score = None
            risk_level = "insufficient_data"
            explanations.append("No usable risk signals")
        else:
            risk_score = sum(
                factors[name] * WEIGHTS[name] for name in factors
            ) / available_weight

            if risk_score >= 70:
                risk_level = "high"
            elif risk_score >= 40:
                risk_level = "medium"
            else:
                risk_level = "low"

            if not explanations:
                explanations.append(
                    "No individual risk trigger crossed its threshold"
                )

        output.append({
            "enrollment_id": row.enrollment_id,
            "student_id": row.student_id,
            "course_id": row.course_id,
            "as_of_date": cutoff.date().isoformat(),
            "attendance_risk": round(
                factors["attendance_risk"], 2
            ) if "attendance_risk" in factors else None,
            "assessment_risk": round(
                factors["assessment_risk"], 2
            ) if "assessment_risk" in factors else None,
            "engagement_risk": round(engagement_risk, 2),
            "risk_score": round(risk_score, 2)
            if risk_score is not None else None,
            "risk_level": risk_level,
            "explanation": "; ".join(explanations),
            "rule_version": "v1",
        })

    result_df = pd.DataFrame(output)
    output_file = data_dir / "risk_scores.csv"
    result_df.to_csv(output_file, index=False)

    print(f"Risk assessment cutoff: {cutoff.date()}")
    print(f"Scored enrollments: {len(result_df)}")
    if not result_df.empty:
        print("\nRisk-level counts:")
        print(result_df["risk_level"].value_counts().to_string())
    print(f"\nSaved results to: {output_file.resolve()}")

    return result_df


if __name__ == "__main__":
    calculate_risk()
