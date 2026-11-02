import json
import math
import pandas as pd
from pathlib import Path

# BuildStock AI - Module 4
# Rule-Based Inventory Decision Engine

ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "data" / "inventory_analysis.csv"
OUTPUT_FILE = ROOT / "data" / "inventory_decisions.csv"
CONFIG_FILE = ROOT / "config" / "inventory_rules.json"

OVERSTOCK_DAYS = 60

DEFAULT_CONFIG = {
    "seasonal_safety_multiplier": 1.2,
    "normal_safety_multiplier": 1.0,
}


def load_config():
    """Load inventory decision settings from JSON."""

    config = DEFAULT_CONFIG.copy()

    if not CONFIG_FILE.exists():
        print("Config file not found. Using default settings.")
        return config

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            user_config = json.load(file)

        if not isinstance(user_config, dict):
            raise ValueError("Configuration must be a JSON object.")

        for key in DEFAULT_CONFIG:
            if key in user_config:
                value = float(user_config[key])

                if not math.isfinite(value) or value <= 0:
                    raise ValueError(
                        f"{key} must be a positive finite number."
                    )

                config[key] = value

    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid configuration: {error}") from error

    return config


def is_seasonal(row):
    """Identify products with high or seasonal demand."""

    if "seasonality" not in row.index:
        return False

    value = str(row["seasonality"]).strip().upper()
    return value in {"HIGH", "SEASONAL", "YES", "TRUE"}


def calculate_thresholds(row, config):
    """Calculate seasonal safety stock and reorder threshold."""

    daily_sales = float(row["avg_daily_sales"])
    lead_time = float(row["lead_time_days"])
    safety_stock = float(row["safety_stock"])
    reorder_level = float(row["reorder_level"])

    multiplier = (
        config["seasonal_safety_multiplier"]
        if is_seasonal(row)
        else config["normal_safety_multiplier"]
    )

    adjusted_safety_stock = math.ceil(safety_stock * multiplier)
    lead_time_demand = daily_sales * lead_time

    required_stock = lead_time_demand + adjusted_safety_stock
    effective_reorder_level = max(reorder_level, required_stock)

    return (
        adjusted_safety_stock,
        lead_time_demand,
        effective_reorder_level,
    )


def classify_product(row, config):
    """Classify inventory using configurable decision rules."""

    stock = float(row["current_stock"])
    daily_sales = float(row["avg_daily_sales"])

    adjusted_safety, _, effective_level = calculate_thresholds(
        row, config
    )

    # Rule 1: Critical stock shortage
    if stock < adjusted_safety:
        return "URGENT REORDER"

    # Rule 2: Excess stock compared with daily demand
    if daily_sales > 0 and stock / daily_sales > OVERSTOCK_DAYS:
        return "OVERSTOCK RISK"

    # Rule 3: Stock may not cover lead-time demand
    if stock <= effective_level:
        return "REORDER SOON"

    # Rule 4: No immediate inventory risk identified
    return "STOCK HEALTHY"


def explain_decision(row, config):
    """Generate a readable explanation for each decision."""

    stock = float(row["current_stock"])
    daily_sales = float(row["avg_daily_sales"])

    adjusted_safety, lead_demand, effective_level = (
        calculate_thresholds(row, config)
    )

    category = row["decision_category"]

    if category == "URGENT REORDER":
        return (
            f"Current stock ({stock:g}) is below adjusted safety "
            f"stock ({adjusted_safety:g}). Prioritize replenishment "
            "and review the suggested quantity."
        )

    if category == "OVERSTOCK RISK":
        days_remaining = stock / daily_sales
        return (
            f"Current stock may last approximately "
            f"{days_remaining:.1f} days, exceeding the "
            f"{OVERSTOCK_DAYS}-day threshold. Review future orders."
        )

    if category == "REORDER SOON":
        return (
            f"Current stock ({stock:g}) is at or below the "
            f"effective reorder threshold ({effective_level:g}). "
            f"Estimated lead-time demand is {lead_demand:g} units. "
            "Plan replenishment and review the suggested quantity."
        )

    return (
        f"Current stock ({stock:g}) is above the effective "
        f"reorder threshold ({effective_level:g}) and does not "
        "exceed the defined overstock threshold. "
        "Continue routine monitoring."
    )


def run_decision_engine():
    print("=" * 65)
    print("BUILDSTOCK AI - MODULE 4")
    print("RULE-BASED INVENTORY DECISION ENGINE")
    print("=" * 65)

    # 1. Check input file
    if not INPUT_FILE.exists():
        print(f"\nERROR: Input file not found:\n{INPUT_FILE}")
        print("Please run Module 3 first.")
        return

    # 2. Read inventory analysis
    try:
        df = pd.read_csv(INPUT_FILE)
    except (OSError, pd.errors.ParserError, UnicodeError, ValueError) as error:
        print(f"\nERROR: Unable to read input file: {error}")
        return

    if df.empty:
        print("\nERROR: The input dataset is empty.")
        return

    # 3. Validate required columns
    required_columns = [
        "product_id",
        "product_name",
        "current_stock",
        "avg_daily_sales",
        "lead_time_days",
        "safety_stock",
        "reorder_level",
    ]

    missing = [column for column in required_columns if column not in df.columns]

    if missing:
        print(f"\nERROR: Missing required columns: {missing}")
        return

    # 4. Validate product identifiers
    for column in ["product_id", "product_name"]:
        if df[column].isna().any():
            print(f"\nERROR: Missing values in {column}.")
            return

        df[column] = df[column].astype(str).str.strip()

        if df[column].eq("").any():
            print(f"\nERROR: Empty values found in {column}.")
            return

    if df["product_id"].duplicated().any():
        duplicates = df.loc[
            df["product_id"].duplicated(keep=False), "product_id"
        ].unique().tolist()

        print(f"\nERROR: Duplicate product IDs: {duplicates}")
        return

    # 5. Validate numeric values
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
        invalid = df[numeric_columns].columns[
            df[numeric_columns].isna().any()
        ].tolist()

        print(f"\nERROR: Missing or invalid numeric values: {invalid}")
        return

    if not df[numeric_columns].map(
        lambda value: math.isfinite(float(value))
    ).all().all():
        print("\nERROR: Infinite or invalid numeric values found.")
        return

    if (df[numeric_columns] < 0).any().any():
        print("\nERROR: Negative inventory values found.")
        return

    if (df["lead_time_days"] <= 0).any():
        print("\nERROR: Lead time must be greater than zero.")
        return

    # 6. Load configuration
    try:
        config = load_config()
    except ValueError as error:
        print(f"\nERROR: {error}")
        return

    print("\nCONFIGURATION")
    print("-" * 40)
    print(
        "Seasonal safety multiplier:",
        config["seasonal_safety_multiplier"],
    )
    print(
        "Normal safety multiplier:",
        config["normal_safety_multiplier"],
    )
    print("Overstock threshold:", OVERSTOCK_DAYS, "days")

    # 7. Calculate decision metrics
    thresholds = df.apply(
        lambda row: calculate_thresholds(row, config),
        axis=1,
    )

    df["adjusted_safety_stock"] = [
        result[0] for result in thresholds
    ]
    df["lead_time_demand"] = [
        result[1] for result in thresholds
    ]
    df["effective_reorder_level"] = [
        result[2] for result in thresholds
    ]

    # 8. Classify each product
    df["decision_category"] = df.apply(
        lambda row: classify_product(row, config),
        axis=1,
    )

    # 9. Explain decisions
    df["decision_reason"] = df.apply(
        lambda row: explain_decision(row, config),
        axis=1,
    )

    # 10. Suggest next action
    action_map = {
        "URGENT REORDER": "Prioritize replenishment",
        "REORDER SOON": "Plan a purchase soon",
        "OVERSTOCK RISK": "Review and reduce future orders",
        "STOCK HEALTHY": "Continue routine monitoring",
    }

    df["recommended_action"] = df["decision_category"].map(action_map)

    # 11. Display decisions
    display_columns = [
        "product_id",
        "product_name",
        "current_stock",
        "adjusted_safety_stock",
        "decision_category",
        "recommended_action",
    ]

    print("\nPRODUCT INVENTORY DECISIONS")
    print("-" * 65)
    print(df[display_columns].to_string(index=False))

    # 12. Display category summary
    category_order = [
        "URGENT REORDER",
        "REORDER SOON",
        "OVERSTOCK RISK",
        "STOCK HEALTHY",
    ]

    summary = df["decision_category"].value_counts().reindex(
        category_order, fill_value=0
    )

    print("\nDECISION SUMMARY")
    print("-" * 40)

    for category, count in summary.items():
        print(f"{category:<22}: {count}")

    # 13. Save results
    try:
        df.to_csv(OUTPUT_FILE, index=False)
    except OSError as error:
        print(f"\nERROR: Could not save output file: {error}")
        return

    print(f"\nOutput saved to:\n{OUTPUT_FILE}")
    print(f"Total products analyzed: {len(df)}")
    print("\nIMPORTANT:")
    print("These are advisory suggestions, not automatic purchase orders.")
    print("Review recommendations before making purchasing decisions.")
    print("\nModule 4 completed successfully!")


if __name__ == "__main__":
    run_decision_engine()
