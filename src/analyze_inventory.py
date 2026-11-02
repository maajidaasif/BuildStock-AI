
import pandas as pd
from pathlib import Path

# BuildStock AI - Module 3
# Inventory Data Analysis

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "construction_products.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "inventory_analysis.csv"


def analyze_inventory():
    print("=" * 60)
    print("BUILDSTOCK AI - MODULE 3")
    print("INVENTORY DATA ANALYSIS")
    print("=" * 60)

    # 1. Load the validated dataset
    if not DATA_FILE.exists():
        print(f"ERROR: Dataset not found: {DATA_FILE}")
        return

    try:
        df = pd.read_csv(DATA_FILE)
    except (OSError, pd.errors.ParserError, UnicodeError) as error:
        print(f"ERROR: Could not read dataset: {error}")
        return

    required = [
        "product_id",
        "product_name",
        "category",
        "unit",
        "current_stock",
        "avg_daily_sales",
        "lead_time_days",
        "safety_stock",
        "reorder_level",
        "seasonality",
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        print(f"ERROR: Missing columns: {missing}")
        return

    if df[required].isna().any().any():
        print("ERROR: Dataset contains missing values.")
        print("Run Module 2 and correct the dataset first.")
        return

    # 2. Convert numerical columns safely
    numeric_columns = [
        "current_stock",
        "avg_daily_sales",
        "lead_time_days",
        "safety_stock",
        "reorder_level",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df[numeric_columns].isna().any().any():
        print("ERROR: Invalid numerical values found.")
        return

    if (df[numeric_columns] < 0).any().any():
        print("ERROR: Negative inventory values found.")
        return

    # 3. Calculate estimated days of stock remaining
    df["days_of_stock_remaining"] = (
        df["current_stock"]
        .div(df["avg_daily_sales"].where(df["avg_daily_sales"] > 0))
    )

    # Products with zero daily sales have no finite estimate
    df["days_of_stock_remaining"] = (
        df["days_of_stock_remaining"].round(2)
    )

    # 4. Calculate stock needed during supplier lead time
    df["expected_lead_time_demand"] = (
        df["avg_daily_sales"] * df["lead_time_days"]
    ).round(2)

    # 5. Calculate stock coverage compared with lead time
    df["stock_covers_lead_time"] = (
        df["days_of_stock_remaining"] >= df["lead_time_days"]
    )

    # 6. Compare current stock with safety stock and reorder level
    df["below_safety_stock"] = (
        df["current_stock"] < df["safety_stock"]
    )

    df["below_reorder_level"] = (
        df["current_stock"] < df["reorder_level"]
    )

    # 7. Identify high-demand products
    df["demand_category"] = "Normal Demand"

    df.loc[
        df["seasonality"].astype(str).str.strip().str.title() == "High",
        "demand_category"
    ] = "High Seasonal Demand"

    df.loc[
        df["avg_daily_sales"] == 0,
        "demand_category"
    ] = "No Recorded Daily Sales"

    # 8. Display analysis results
    display_columns = [
        "product_id",
        "product_name",
        "current_stock",
        "avg_daily_sales",
        "days_of_stock_remaining",
        "lead_time_days",
        "below_safety_stock",
        "below_reorder_level",
        "demand_category",
    ]

    print("\nINVENTORY ANALYSIS RESULTS\n")
    print(
        df[display_columns].to_string(
            index=False,
            na_rep="N/A"
        )
    )

    # 9. Save analysis to a separate CSV file
    df.to_csv(OUTPUT_FILE, index=False)

    # 10. Print summary
    zero_sales = int((df["avg_daily_sales"] == 0).sum())
    low_safety = int(df["below_safety_stock"].sum())
    low_reorder = int(df["below_reorder_level"].sum())
    high_demand = int(
        (df["demand_category"] == "High Seasonal Demand").sum()
    )

    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Products analyzed: {len(df)}")
    print(f"Below safety stock: {low_safety}")
    print(f"Below reorder level: {low_reorder}")
    print(f"High seasonal demand products: {high_demand}")
    print(f"Products with zero daily sales: {zero_sales}")
    print(f"\nAnalysis saved to: {OUTPUT_FILE}")
    print("\nModule 3 analysis completed successfully!")


if __name__ == "__main__":
    analyze_inventory()
