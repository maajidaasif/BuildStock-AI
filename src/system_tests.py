
import math
import pandas as pd
from pathlib import Path

# ============================================================
# BUILDSTOCK AI - MODULE 9
# DATA QUALITY AND SYSTEM TESTING
# ============================================================

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

FILES = {
    "Dataset": DATA_DIR / "construction_products.csv",
    "Inventory Analysis": DATA_DIR / "inventory_analysis.csv",
    "Inventory Decisions": DATA_DIR / "inventory_decisions.csv",
    "Reorder Recommendations": DATA_DIR / "reorder_recommendations.csv",
    "AI Explanations": DATA_DIR / "ai_inventory_explanations.csv",
    "Inventory Alerts": DATA_DIR / "inventory_alerts.csv",
}

REQUIRED_COLUMNS = {
    "Dataset": [
        "product_id",
        "product_name",
        "category",
        "unit",
        "current_stock",
        "avg_daily_sales",
        "lead_time_days",
        "safety_stock",
    ],
    "Inventory Analysis": ["product_id"],
    "Inventory Decisions": [
        "product_id",
        "decision_category",
    ],
    "Reorder Recommendations": [
        "product_id",
        "recommended_reorder_quantity",
        "decision_category",
    ],
    "AI Explanations": [
        "product_id",
        "ai_explanation",
    ],
    "Inventory Alerts": [
        "product_id",
        "priority",
        "alert_message",
        "decision_category",
        "recommended_reorder_quantity",
    ],
}

VALID_STATUSES = {
    "STOCK HEALTHY",
    "REORDER SOON",
    "URGENT REORDER",
    "OVERSTOCK RISK",
}

REORDER_STATUSES = {
    "URGENT REORDER",
    "REORDER SOON",
}

EXPECTED_PRIORITIES = {
    "URGENT REORDER": "P1 - CRITICAL",
    "REORDER SOON": "P2 - HIGH",
    "OVERSTOCK RISK": "P3 - REVIEW",
    "STOCK HEALTHY": "P4 - NORMAL",
}


# ============================================================
# TEST HELPER FUNCTIONS
# ============================================================

def check(condition, description):
    """Print the result of an individual test."""

    if condition:
        print(f"[PASS] {description}")
        return True

    print(f"[FAIL] {description}")
    return False


def is_numeric_and_finite(series):
    """Return True when every value is numeric and finite."""

    values = pd.to_numeric(series, errors="coerce")

    return bool(
        values.notna().all()
        and values.map(
            lambda value: math.isfinite(float(value))
        ).all()
    )


def same_product_ids(first, second):
    """Compare product ID sets after basic normalization."""

    first_ids = set(first.dropna().astype(str).str.strip())
    second_ids = set(second.dropna().astype(str).str.strip())

    return first_ids == second_ids


# ============================================================
# MAIN TEST RUNNER
# ============================================================

def main():
    print("=" * 70)
    print("BUILDSTOCK AI - MODULE 9")
    print("DATA QUALITY AND SYSTEM TESTING")
    print("=" * 70)

    passed = 0
    failed = 0
    dataframes = {}

    def run_test(condition, description):
        nonlocal passed, failed

        result = check(bool(condition), description)

        if result:
            passed += 1
        else:
            failed += 1

    # --------------------------------------------------------
    # 1. FILE AVAILABILITY
    # --------------------------------------------------------

    print("\n1. FILE AVAILABILITY")
    print("-" * 70)

    for name, path in FILES.items():
        exists = path.exists()

        run_test(
            exists,
            f"{name} file exists",
        )

        if exists:
            try:
                dataframes[name] = pd.read_csv(path)

            except (
                OSError,
                ValueError,
                pd.errors.ParserError,
                UnicodeDecodeError,
            ) as error:
                run_test(
                    False,
                    f"{name} file can be read: {error}",
                )

    essential_files = [
        "Dataset",
        "Inventory Decisions",
        "Reorder Recommendations",
        "AI Explanations",
        "Inventory Alerts",
    ]

    missing_files = [
        name
        for name in essential_files
        if name not in dataframes
    ]

    if missing_files:
        print("\nCannot run all tests.")
        print("Missing or unreadable files:", missing_files)
        print(f"Tests passed: {passed}")
        print(f"Tests failed: {failed}")
        print("Repair the required files and run the tests again.")
        return

    # --------------------------------------------------------
    # 2. COLUMN AND DATA VALIDATION
    # --------------------------------------------------------

    print("\n2. DATA VALIDATION")
    print("-" * 70)

    for name, required_columns in REQUIRED_COLUMNS.items():
        if name not in dataframes:
            run_test(
                False,
                f"{name} data is available",
            )
            continue

        missing_columns = [
            column
            for column in required_columns
            if column not in dataframes[name].columns
        ]

        run_test(
            not missing_columns,
            f"{name} has all required columns"
            + (
                f"; missing: {missing_columns}"
                if missing_columns
                else ""
            ),
        )

    dataset = dataframes["Dataset"]
    decisions = dataframes["Inventory Decisions"]
    recommendations = dataframes["Reorder Recommendations"]
    explanations = dataframes["AI Explanations"]
    alerts = dataframes["Inventory Alerts"]

    # Stop if required columns are missing, preventing misleading
    # follow-up errors while testing the data.
    required_data_columns = {
        "Dataset": set(REQUIRED_COLUMNS["Dataset"]),
        "Inventory Decisions": set(
            REQUIRED_COLUMNS["Inventory Decisions"]
        ),
        "Reorder Recommendations": set(
            REQUIRED_COLUMNS["Reorder Recommendations"]
        ),
        "AI Explanations": set(
            REQUIRED_COLUMNS["AI Explanations"]
        ),
        "Inventory Alerts": set(
            REQUIRED_COLUMNS["Inventory Alerts"]
        ),
    }

    missing_required = []

    for name, required in required_data_columns.items():
        available = set(dataframes[name].columns)
        missing = required - available

        if missing:
            missing_required.append(
                f"{name}: {sorted(missing)}"
            )

    if missing_required:
        print("\nCannot run dependent tests because columns are missing:")
        for item in missing_required:
            print(f"- {item}")

        print(f"\nTests passed: {passed}")
        print(f"Tests failed: {failed}")
        return

    run_test(
        not dataset.empty,
        "Dataset is not empty",
    )

    run_test(
        dataset["product_id"].notna().all()
        and dataset["product_id"].astype(str).str.strip().ne("").all()
        and dataset["product_id"].is_unique,
        "Dataset product IDs are present and unique",
    )

    run_test(
        dataset["product_name"].notna().all()
        and dataset["product_name"].astype(str).str.strip().ne("").all(),
        "All products have names",
    )

    run_test(
        dataset["unit"].notna().all()
        and dataset["unit"].astype(str).str.strip().ne("").all(),
        "All products have units",
    )

    dataset_numeric_columns = [
        "current_stock",
        "avg_daily_sales",
        "lead_time_days",
        "safety_stock",
    ]

    numeric_data = dataset[
        dataset_numeric_columns
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    numeric_valid = bool(
        numeric_data.notna().all().all()
        and numeric_data.map(
            lambda value: math.isfinite(float(value))
        ).all().all()
    )

    run_test(
        numeric_valid,
        "Stock, sales, lead time and safety stock are numeric and finite",
    )

    if numeric_valid:
        run_test(
            (numeric_data >= 0).all().all(),
            "Inventory numeric values are non-negative",
        )

        run_test(
            (numeric_data["lead_time_days"] >= 1).all(),
            "Lead time is at least one day",
        )

    # --------------------------------------------------------
    # 3. INVENTORY DECISION TESTS
    # --------------------------------------------------------

    print("\n3. INVENTORY DECISION TESTS")
    print("-" * 70)

    decisions["product_id"] = (
        decisions["product_id"].astype(str).str.strip()
    )

    dataset["product_id"] = (
        dataset["product_id"].astype(str).str.strip()
    )

    recommendations["product_id"] = (
        recommendations["product_id"].astype(str).str.strip()
    )

    explanations["product_id"] = (
        explanations["product_id"].astype(str).str.strip()
    )

    alerts["product_id"] = (
        alerts["product_id"].astype(str).str.strip()
    )

    decision_statuses = (
        decisions["decision_category"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    invalid_statuses = (
        set(decision_statuses.unique())
        - VALID_STATUSES
    )

    if invalid_statuses:
        status_description = (
            f"Invalid inventory statuses found: "
            f"{sorted(invalid_statuses)}"
        )
    else:
        actual_statuses = sorted(
            decision_statuses.unique()
        )

        status_description = (
            f"All inventory statuses are valid: "
            f"{actual_statuses}"
        )

    run_test(
        not invalid_statuses,
        status_description,
    )

    run_test(
        decision_statuses.ne("").all(),
        "Every product has a decision status",
    )

    run_test(
        decisions["product_id"].notna().all()
        and decisions["product_id"].ne("").all()
        and decisions["product_id"].is_unique,
        "Inventory decision IDs are present and unique",
    )

    run_test(
        same_product_ids(
            dataset["product_id"],
            decisions["product_id"],
        ),
        "Dataset and inventory decisions contain the same products",
    )

    # --------------------------------------------------------
    # 4. REORDER RECOMMENDATION TESTS
    # --------------------------------------------------------

    print("\n4. REORDER RECOMMENDATION TESTS")
    print("-" * 70)

    quantity_column = "recommended_reorder_quantity"

    quantities = pd.to_numeric(
        recommendations[quantity_column],
        errors="coerce",
    )

    quantities_valid = is_numeric_and_finite(
        recommendations[quantity_column]
    )

    run_test(
        quantities_valid,
        "Reorder quantities are numeric and finite",
    )

    if quantities_valid:
        run_test(
            (quantities >= 0).all(),
            "No negative reorder quantities exist",
        )

    run_test(
        recommendations["product_id"].notna().all()
        and recommendations["product_id"].ne("").all()
        and recommendations["product_id"].is_unique,
        "Reorder recommendation IDs are present and unique",
    )

    run_test(
        same_product_ids(
            dataset["product_id"],
            recommendations["product_id"],
        ),
        "Dataset and reorder recommendations contain the same products",
    )

    run_test(
        same_product_ids(
            decisions["product_id"],
            recommendations["product_id"],
        ),
        "Decisions and recommendations contain the same products",
    )

    # Check that Modules 4 and 5 agree on the status of each product.
    decision_status_map = decisions.set_index(
        "product_id"
    )["decision_category"].sort_index()

    recommendation_status_map = recommendations.set_index(
        "product_id"
    )["decision_category"].sort_index()

    statuses_match = (
        decision_status_map.index.equals(
            recommendation_status_map.index
        )
        and decision_status_map.equals(
            recommendation_status_map
        )
    )

    run_test(
        statuses_match,
        "Decision statuses match between Modules 4 and 5",
    )

    if quantities_valid:
        checked = recommendations.copy()
        checked["_test_quantity"] = quantities

        checked_statuses = (
            checked["decision_category"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        reorder_rows = checked_statuses.isin(
            REORDER_STATUSES
        )

        non_reorder_rows = checked_statuses.isin(
            VALID_STATUSES - REORDER_STATUSES
        )

        run_test(
            (
                checked.loc[
                    reorder_rows,
                    "_test_quantity",
                ] > 0
            ).all(),
            "Every URGENT REORDER / REORDER SOON product has a positive quantity",
        )

        run_test(
            (
                checked.loc[
                    non_reorder_rows,
                    "_test_quantity",
                ] == 0
            ).all()
            and (
                reorder_rows | non_reorder_rows
            ).all(),
            "Healthy and overstock products have zero reorder quantity",
        )

    # --------------------------------------------------------
    # 5. AI EXPLANATION TESTS
    # --------------------------------------------------------

    print("\n5. AI EXPLANATION TESTS")
    print("-" * 70)

    explanation_text = (
        explanations["ai_explanation"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    run_test(
        explanation_text.ne("").all(),
        "Every product has a non-empty AI explanation",
    )

    run_test(
        explanations["product_id"].notna().all()
        and explanations["product_id"].ne("").all()
        and explanations["product_id"].is_unique,
        "AI explanation IDs are present and unique",
    )

    run_test(
        same_product_ids(
            dataset["product_id"],
            explanations["product_id"],
        ),
        "Dataset and AI explanations contain the same products",
    )

    # Check the LLM source label if Module 6 provides it.
    if "explanation_source" in explanations.columns:
        source_values = (
            explanations["explanation_source"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        run_test(
            source_values.ne("").all(),
            "Every explanation has a recorded source",
        )

        print("\nExplanation source counts:")
        print(source_values.value_counts().to_string())

    # Compare saved explanation statuses and quantities with
    # the rule-based decision/recommendation files.
    if {
        "decision_category",
        "recommended_reorder_quantity",
    }.issubset(explanations.columns):
        explanation_check = explanations[
            [
                "product_id",
                "decision_category",
                "recommended_reorder_quantity",
            ]
        ].copy()

        authoritative = recommendations[
            [
                "product_id",
                "decision_category",
                "recommended_reorder_quantity",
            ]
        ].copy()

        explanation_check["recommended_reorder_quantity"] = (
            pd.to_numeric(
                explanation_check["recommended_reorder_quantity"],
                errors="coerce",
            )
        )

        authoritative["recommended_reorder_quantity"] = (
            pd.to_numeric(
                authoritative["recommended_reorder_quantity"],
                errors="coerce",
            )
        )

        merged = explanation_check.merge(
            authoritative,
            on="product_id",
            how="outer",
            suffixes=("_explanation", "_recommendation"),
            indicator=True,
            validate="one_to_one",
        )

        statuses_consistent = (
            merged["_merge"].eq("both").all()
            and merged["decision_category_explanation"].equals(
                merged["decision_category_recommendation"]
            )
        )

        run_test(
            statuses_consistent,
            "AI output statuses match rule-based recommendations",
        )

        quantities_consistent = (
            merged["_merge"].eq("both").all()
            and merged[
                "recommended_reorder_quantity_explanation"
            ].notna().all()
            and merged[
                "recommended_reorder_quantity_recommendation"
            ].notna().all()
            and (
                merged[
                    "recommended_reorder_quantity_explanation"
                ]
                ==
                merged[
                    "recommended_reorder_quantity_recommendation"
                ]
            ).all()
        )

        run_test(
            quantities_consistent,
            "AI output quantities match rule-based recommendations",
        )

    # --------------------------------------------------------
    # 6. INVENTORY ALERT TESTS
    # --------------------------------------------------------

    print("\n6. INVENTORY ALERT TESTS")
    print("-" * 70)

    run_test(
        alerts["priority"].notna().all()
        and alerts["priority"].astype(str).str.strip().ne("").all(),
        "Every alert has a priority",
    )

    run_test(
        alerts["alert_message"].notna().all()
        and alerts["alert_message"].astype(str).str.strip().ne("").all(),
        "Every alert has a message",
    )

    run_test(
        alerts["product_id"].notna().all()
        and alerts["product_id"].ne("").all()
        and alerts["product_id"].is_unique,
        "Inventory alert IDs are present and unique",
    )

    run_test(
        same_product_ids(
            dataset["product_id"],
            alerts["product_id"],
        ),
        "Dataset and inventory alerts contain the same products",
    )

    alert_priorities_valid = alerts.apply(
        lambda row: (
            EXPECTED_PRIORITIES.get(
                str(row["decision_category"]).strip()
            )
            == str(row["priority"]).strip()
        ),
        axis=1,
    )

    run_test(
        alert_priorities_valid.all(),
        "Alert priorities match their decision categories",
    )

    alert_quantities = pd.to_numeric(
        alerts["recommended_reorder_quantity"],
        errors="coerce",
    )

    alert_quantities_valid = is_numeric_and_finite(
        alerts["recommended_reorder_quantity"]
    )

    run_test(
        alert_quantities_valid,
        "Alert reorder quantities are numeric and finite",
    )

    if alert_quantities_valid and quantities_valid:
        recommendation_quantity_map = recommendations.set_index(
            "product_id"
        )[quantity_column]

        expected_quantities = alerts["product_id"].map(
            recommendation_quantity_map
        )

        alert_quantities_match = (
            expected_quantities.notna().all()
            and (
                alert_quantities.reset_index(drop=True)
                == pd.to_numeric(
                    expected_quantities,
                    errors="coerce",
                ).reset_index(drop=True)
            ).all()
        )

        run_test(
            alert_quantities_match,
            "Alert quantities match Module 5 recommendations",
        )

    # --------------------------------------------------------
    # 7. FINAL REPORT
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("MODULE 9 TEST SUMMARY")
    print("=" * 70)

    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")

    if failed == 0:
        print("\nRESULT: ALL TESTS PASSED")
        print(
            "BuildStock AI passed the configured data-quality "
            "and cross-module consistency checks."
        )
    else:
        print("\nRESULT: SOME TESTS FAILED")
        print(
            "Review each [FAIL] message before treating "
            "the pipeline as verified."
        )

    print("\nIMPORTANT LIMITATIONS:")
    print("- These tests do not prove every business formula is correct.")
    print("- They do not verify every factual claim generated by the LLM.")
    print("- Human review is required before purchasing materials.")
    print("=" * 70)


if __name__ == "__main__":
    main()
