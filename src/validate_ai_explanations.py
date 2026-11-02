import math
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

EXPLANATIONS_FILE = DATA_DIR / "ai_inventory_explanations.csv"
RECOMMENDATIONS_FILE = DATA_DIR / "reorder_recommendations.csv"
OUTPUT_FILE = DATA_DIR / "ai_explanation_validation.csv"


def normalize_text(value):
    return re.sub(r"\s+", " ", str(value)).strip().lower()


def validate_files():
    for file_path in [EXPLANATIONS_FILE, RECOMMENDATIONS_FILE]:
        if not file_path.exists():
            raise FileNotFoundError(f"Required file not found: {file_path}")


def validate_ai_explanations():
    validate_files()

    ai_df = pd.read_csv(EXPLANATIONS_FILE)
    recommendations_df = pd.read_csv(RECOMMENDATIONS_FILE)

    required_ai = {
        "product_id",
        "ai_explanation",
        "decision_category",
        "recommended_reorder_quantity",
    }

    required_recommendations = {
        "product_id",
        "decision_category",
        "recommended_reorder_quantity",
    }

    missing_ai = required_ai - set(ai_df.columns)
    missing_recommendations = (
        required_recommendations - set(recommendations_df.columns)
    )

    if missing_ai:
        raise ValueError(
            f"AI explanation file is missing columns: {sorted(missing_ai)}"
        )

    if missing_recommendations:
        raise ValueError(
            "Recommendation file is missing columns: "
            f"{sorted(missing_recommendations)}"
        )

    if ai_df["product_id"].duplicated().any():
        raise ValueError("Duplicate product IDs in AI explanations.")

    if recommendations_df["product_id"].duplicated().any():
        raise ValueError("Duplicate product IDs in recommendations.")

    merged = ai_df.merge(
        recommendations_df[
            [
                "product_id",
                "decision_category",
                "recommended_reorder_quantity",
            ]
        ],
        on="product_id",
        how="outer",
        suffixes=("_ai", "_rule"),
        indicator=True,
        validate="one_to_one",
    )

    results = []

    for _, row in merged.iterrows():
        issues = []

        if row["_merge"] != "both":
            issues.append("Product missing from one input file")
        else:
            ai_status = normalize_text(row["decision_category_ai"])
            rule_status = normalize_text(row["decision_category_rule"])

            if ai_status != rule_status:
                issues.append("Decision status does not match rule engine")

            try:
                ai_qty = float(row["recommended_reorder_quantity_ai"])
                rule_qty = float(row["recommended_reorder_quantity_rule"])

                if not math.isfinite(ai_qty) or not math.isfinite(rule_qty):
                    issues.append("Reorder quantity is not finite")
                elif not math.isclose(ai_qty, rule_qty, abs_tol=1e-9):
                    issues.append("Reorder quantity does not match rule engine")
            except (TypeError, ValueError):
                issues.append("Reorder quantity is not numeric")

        explanation = row.get("ai_explanation", "")

        if pd.isna(explanation) or not str(explanation).strip():
            issues.append("AI explanation is empty")

        results.append({
            "product_id": row["product_id"],
            "validation_status": "PASS" if not issues else "REVIEW REQUIRED",
            "validation_issues": "; ".join(issues) if issues else "None",
            "decision_category": row.get("decision_category_rule", ""),
            "recommended_reorder_quantity": row.get(
                "recommended_reorder_quantity_rule", ""
            ),
            "ai_explanation": explanation,
        })

    result_df = pd.DataFrame(results)
    result_df.to_csv(OUTPUT_FILE, index=False)

    passed = (result_df["validation_status"] == "PASS").sum()
    review = (result_df["validation_status"] == "REVIEW REQUIRED").sum()

    print("=" * 65)
    print("BUILDSTOCK AI - MODULE 10")
    print("AI EXPLANATION VALIDATION")
    print("=" * 65)
    print(f"Products checked: {len(result_df)}")
    print(f"Passed structural checks: {passed}")
    print(f"Products requiring review: {review}")
    print(f"Validation report: {OUTPUT_FILE}")
    print()
    print("IMPORTANT:")
    print("This module checks data consistency and empty explanations.")
    print("It does NOT prove every numerical statement in the LLM text")
    print("is factually correct. Human review is still required.")
    print("=" * 65)


if __name__ == "__main__":
    try:
        validate_ai_explanations()
    except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
        print(f"VALIDATION ERROR: {error}")
