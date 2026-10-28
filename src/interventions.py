"""Create traceable support cases and interventions from risk scores."""

from pathlib import Path

import pandas as pd


def generate_interventions(data_dir="data/generated"):
    data_path = Path(data_dir)

    risk_file = data_path / "risk_scores.csv"
    enrollment_file = data_path / "enrollments.csv"

    if not risk_file.exists() or not enrollment_file.exists():
        raise FileNotFoundError(
            "Run the data generator and risk engine before generating interventions."
        )

    risks = pd.read_csv(risk_file)
    enrollments = pd.read_csv(enrollment_file)

    # Support either common naming convention for risk score and risk level.
    score_column = "risk_score" if "risk_score" in risks.columns else "score"
    level_column = "risk_level" if "risk_level" in risks.columns else "level"

    required_risk_columns = {
        "enrollment_id",
        score_column,
        level_column,
        "as_of_date",
        "rule_version",
    }
    missing = required_risk_columns - set(risks.columns)
    if missing:
        raise ValueError(f"Risk scores are missing required columns: {sorted(missing)}")

    required_enrollment_columns = {
        "enrollment_id",
        "student_id",
        "course_id",
        "status",
    }
    missing = required_enrollment_columns - set(enrollments.columns)
    if missing:
        raise ValueError(
            f"Enrollments are missing required columns: {sorted(missing)}"
        )

    # Only create interventions for active enrollments with actionable risk.
    eligible = risks.merge(
        enrollments[["enrollment_id", "status"]],
        on="enrollment_id",
        how="inner",
        validate="one_to_one",
    )

    eligible = eligible[
        eligible["status"].eq("active")
        & eligible[level_column].isin(["high", "medium"])
    ].copy()

    support_cases = []
    interventions = []

    for number, row in enumerate(
        eligible.sort_values("enrollment_id").to_dict("records"), start=1
    ):
        level = row[level_column]
        score = float(row[score_column])
        trigger_date = str(row["as_of_date"])[:10]
        rule_version = str(row["rule_version"])

        case_id = f"SUP-2026-{number:06d}"
        intervention_id = f"INT-2026-{number:06d}"

        priority = "urgent" if level == "high" else "normal"

        support_cases.append(
            {
                "support_case_id": case_id,
                "student_id": row["student_id"],
                "enrollment_id": row["enrollment_id"],
                "course_id": row["course_id"],
                "opened_date": trigger_date,
                "case_type": "academic_risk",
                "severity": level,
                "status": "open",
                "source": "risk_engine",
                "description": (
                    f"Risk score {score:.1f}; review the recorded risk factors."
                ),
            }
        )

        interventions.append(
            {
                "intervention_id": intervention_id,
                "support_case_id": case_id,
                "student_id": row["student_id"],
                "enrollment_id": row["enrollment_id"],
                "trigger_date": trigger_date,
                "intervention_date": trigger_date,
                "intervention_type": (
                    "advisor_meeting" if level == "high" else "support_check_in"
                ),
                "priority": priority,
                "status": "planned",
                "trigger_score": round(score, 2),
                "trigger_level": level,
                "rule_version": rule_version,
                "rationale": (
                    str(row.get("explanation", "Risk threshold reached"))
                    if pd.notna(row.get("explanation", "Risk threshold reached"))
                    else "Risk threshold reached"
                ),
            }
        )

    case_columns = [
        "support_case_id", "student_id", "enrollment_id", "course_id",
        "opened_date", "case_type", "severity", "status", "source", "description",
    ]
    intervention_columns = [
        "intervention_id", "support_case_id", "student_id", "enrollment_id",
        "trigger_date", "intervention_date", "intervention_type", "priority",
        "status", "trigger_score", "trigger_level", "rule_version", "rationale",
    ]

    pd.DataFrame(support_cases, columns=case_columns).to_csv(
        data_path / "support_cases.csv", index=False
    )
    pd.DataFrame(interventions, columns=intervention_columns).to_csv(
        data_path / "interventions.csv", index=False
    )

    print(f"Support cases created: {len(support_cases)}")
    print(f"Interventions planned: {len(interventions)}")
    print(f"Saved files to: {data_path.resolve()}")

    return support_cases, interventions


if __name__ == "__main__":
    generate_interventions()