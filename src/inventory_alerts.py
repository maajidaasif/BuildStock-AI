
import pandas as pd
from pathlib import Path

# BuildStock AI - Inventory Alerts and Risk Prioritization

ROOT = Path(__file__).resolve().parent.parent

DECISIONS_FILE = ROOT / "data" / "inventory_decisions.csv"
RECOMMENDATIONS_FILE = ROOT / "data" / "reorder_recommendations.csv"
OUTPUT_FILE = ROOT / "data" / "inventory_alerts.csv"

VALID_STATUSES = {
    "URGENT REORDER",
    "REORDER SOON",
    "OVERSTOCK RISK",
    "NO SALES - REVIEW REQUIRED",
    "STOCK HEALTHY",
}


def assign_priority(row):
    """Assign priority based on the inventory decision."""

    status = row["decision_category"]

    if status == "URGENT REORDER":
        return "P1 - CRITICAL"

    if status == "REORDER SOON":
        return "P2 - HIGH"

    if status in {
        "OVERSTOCK RISK",
        "NO SALES - REVIEW REQUIRED",
    }:
        return "P3 - REVIEW"

    return "P4 - NORMAL"


def create_alert(row):
    """Generate an alert consistent with status and quantity."""

    status = row["decision_category"]
    quantity = float(row["recommended_reorder_quantity"])
    unit = str(row["unit"]).strip()

    if status == "URGENT REORDER":

        if quantity > 0:
            return (
                "URGENT: Current stock is below safety stock. "
                f"Review replenishment of {quantity:g} {unit} "
                "as a priority."
            )

        return (
            "URGENT: Current stock is below safety stock, "
            "but the calculated reorder quantity is zero. "
            "Review inventory inputs immediately."
        )

    if status == "REORDER SOON":

        if quantity > 0:
            return (
                "HIGH: Stock has reached the reorder zone. "
                f"Review replenishment of {quantity:g} {unit}."
            )

        return (
            "HIGH: Stock has reached the reorder zone, but "
            "the calculated quantity is zero. Review the "
            "reorder threshold and demand inputs."
        )

    if status == "OVERSTOCK RISK":
        return (
            "REVIEW: Stock may exceed expected demand. "
            "Review upcoming purchases before replenishing."
        )

    if status == "NO SALES - REVIEW REQUIRED":
        return (
            "REVIEW: No daily sales are recorded for this product. "
            "Review sales history, demand and current stock before "
            "making any replenishment decision. "
            "Do not reorder automatically."
        )

    return (
        "NORMAL: Stock is classified as healthy. "
        "Continue routine inventory monitoring."
    )


def run_inventory_alerts():

    print("=" * 65)
    print("BUILDSTOCK AI - INVENTORY ALERTS")
    print("INVENTORY ALERTS AND RISK PRIORITIZATION")
    print("=" * 65)

    # Step 1: Check input files

    for file_path in [DECISIONS_FILE, RECOMMENDATIONS_FILE]:

        if not file_path.exists():
            print(f"\nERROR: Required file not found:\n{file_path}")
            print("Run Modules 4 and 5 first.")
            return

    # Step 2: Load input files

    try:
        decisions = pd.read_csv(DECISIONS_FILE)
        recommendations = pd.read_csv(RECOMMENDATIONS_FILE)

    except (
        OSError,
        ValueError,
        pd.errors.ParserError,
        UnicodeError,
    ) as error:

        print(f"\nERROR: Could not read input files: {error}")
        return

    if decisions.empty or recommendations.empty:
        print("\nERROR: An input dataset is empty.")
        return

    # Step 3: Validate required columns

    decision_columns = [
        "product_id",
        "product_name",
        "current_stock",
        "safety_stock",
        "decision_category",
    ]

    recommendation_columns = [
        "product_id",
        "unit",
        "recommended_reorder_quantity",
    ]

    missing_decisions = [
        col for col in decision_columns
        if col not in decisions.columns
    ]

    missing_recommendations = [
        col for col in recommendation_columns
        if col not in recommendations.columns
    ]

    if missing_decisions:
        print(
            "\nERROR: Missing decision columns: "
            f"{missing_decisions}"
        )
        return

    if missing_recommendations:
        print(
            "\nERROR: Missing recommendation columns: "
            f"{missing_recommendations}"
        )
        return

    # Step 4: Validate product IDs

    for label, frame in [
        ("decisions", decisions),
        ("recommendations", recommendations),
    ]:

        if frame["product_id"].isna().any():
            print(f"\nERROR: Missing product IDs in {label}.")
            return

        frame["product_id"] = (
            frame["product_id"].astype(str).str.strip()
        )

        if frame["product_id"].eq("").any():
            print(f"\nERROR: Empty product IDs in {label}.")
            return

        if frame["product_id"].duplicated().any():
            print(f"\nERROR: Duplicate product IDs in {label}.")
            return

    # Step 5: Verify product IDs match

    decision_ids = set(decisions["product_id"])
    recommendation_ids = set(recommendations["product_id"])

    if decision_ids != recommendation_ids:

        print(
            "\nERROR: Product IDs do not match between "
            "decision and recommendation files."
        )

        print(f"Only in decisions: {decision_ids - recommendation_ids}")

        print(
            "Only in recommendations: "
            f"{recommendation_ids - decision_ids}"
        )

        return

    # Step 6: Merge inventory data

    decisions = decisions.drop(
        columns=["unit"],
        errors="ignore",
    )

    try:

        df = decisions.merge(
            recommendations[
                [
                    "product_id",
                    "unit",
                    "recommended_reorder_quantity",
                ]
            ],
            on="product_id",
            how="inner",
            validate="one_to_one",
        )

    except (ValueError, pd.errors.MergeError) as error:

        print(f"\nERROR: Could not merge inventory data: {error}")
        return

    if len(df) != len(decisions):
        print("\nERROR: Some products were lost during merging.")
        return

    # Step 7: Validate product information

    if (
        df["product_name"].isna().any()
        or df["product_name"].astype(str).str.strip().eq("").any()
    ):
        print("\nERROR: Product names are missing or empty.")
        return

    if (
        df["unit"].isna().any()
        or df["unit"].astype(str).str.strip().eq("").any()
    ):
        print("\nERROR: Product units are missing or empty.")
        return

    if df["decision_category"].isna().any():
        print("\nERROR: Missing inventory decision categories.")
        return

    df["decision_category"] = (
        df["decision_category"].astype(str).str.strip()
    )

    invalid_statuses = (
        set(df["decision_category"].unique()) - VALID_STATUSES
    )

    if invalid_statuses:
        print(f"\nERROR: Invalid decision categories: {invalid_statuses}")
        return

    # Step 8: Validate numerical values

    numeric_columns = [
        "current_stock",
        "safety_stock",
        "recommended_reorder_quantity",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if df[numeric_columns].isna().any().any():
        print("\nERROR: Missing or invalid numerical values.")
        return

    if (df[numeric_columns] < 0).any().any():
        print("\nERROR: Negative inventory values found.")
        return

    # Step 9: Generate priorities and alerts

    df["priority"] = df.apply(assign_priority, axis=1)

    df["alert_message"] = df.apply(create_alert, axis=1)

    priority_order = {
        "P1 - CRITICAL": 1,
        "P2 - HIGH": 2,
        "P3 - REVIEW": 3,
        "P4 - NORMAL": 4,
    }

    df["priority_order"] = df["priority"].map(priority_order)

    df = df.sort_values(
        by=["priority_order", "product_name"],
        ascending=[True, True],
    ).reset_index(drop=True)

    # Step 10: Display alerts

    display_columns = [
        "product_id",
        "product_name",
        "decision_category",
        "priority",
        "recommended_reorder_quantity",
        "unit",
        "alert_message",
    ]

    print("\nINVENTORY ALERTS")
    print("-" * 65)

    print(
        df[display_columns].to_string(index=False)
    )

    # Step 11: Priority summary

    print("\nPRIORITY SUMMARY")
    print("-" * 40)

    for priority in [
        "P1 - CRITICAL",
        "P2 - HIGH",
        "P3 - REVIEW",
        "P4 - NORMAL",
    ]:

        count = (df["priority"] == priority).sum()

        print(f"{priority:<18}: {count}")

    # Step 12: No-sales summary

    no_sales_count = (
        df["decision_category"]
        == "NO SALES - REVIEW REQUIRED"
    ).sum()

    print("\nNO-SALES REVIEW SUMMARY")
    print("-" * 40)
    print(f"Products requiring manual review: {no_sales_count}")

    # Step 13: Save output

    try:

        df.to_csv(
            OUTPUT_FILE,
            index=False,
        )

    except OSError as error:

        print(f"\nERROR: Could not save alerts: {error}")
        return

    print(f"\nAlerts saved to:\n{OUTPUT_FILE}")

    print("\nInventory alert module completed successfully!")

    print(
        "Note: Alerts are recommendations. "
        "A human must review decisions before purchasing."
    )


if __name__ == "__main__":
    run_inventory_alerts()
