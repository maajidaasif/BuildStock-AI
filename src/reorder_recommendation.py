
"""
BuildStock AI - Module 5
Reorder Quantity Recommendation

Baseline mentor formula:
    (Average Daily Sales * Lead Time) + Safety Stock - Current Stock

Seasonality can increase the safety buffer through JSON configuration.
Recommendations are advisory; purchases are never placed automatically.
"""

from pathlib import Path
import json
import math

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "config" / "inventory_rules.json"

DATASET_FILE = DATA_DIR / "construction_products.csv"
DECISIONS_FILE = DATA_DIR / "inventory_decisions.csv"
OUTPUT_FILE = DATA_DIR / "reorder_recommendations.csv"

REQUIRED_DATA_COLUMNS = [
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

REQUIRED_DECISION_COLUMNS = ["product_id", "decision_category"]

REORDER_STATUSES = {"URGENT REORDER", "REORDER SOON"}
VALID_STATUSES = REORDER_STATUSES | {
    "OVERSTOCK RISK",
    "STOCK HEALTHY",
}

NUMERIC_COLUMNS = [
    "current_stock",
    "avg_daily_sales",
    "lead_time_days",
    "safety_stock",
    "reorder_level",
]


def load_config():
    """Read optional configuration; use safe defaults if absent."""
    config = {
        "seasonal_safety_multiplier": 1.2,
        "normal_safety_multiplier": 1.0,
    }

    if not CONFIG_FILE.exists():
        return config

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            supplied = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid inventory rules JSON: {error}") from error

    for key in config:
        if key in supplied:
            try:
                config[key] = float(supplied[key])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Configuration '{key}' must be numeric."
                ) from error

        if not math.isfinite(config[key]) or config[key] <= 0:
            raise ValueError(
                f"Configuration '{key}' must be a positive finite number."
            )

    return config


def load_and_validate_data():
    """Load product and decision CSV files and validate their contents."""
    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_FILE}\n"
            "Run: python src/create_dataset.py"
        )

    if not DECISIONS_FILE.exists():
        raise FileNotFoundError(
            f"Decision file not found: {DECISIONS_FILE}\n"
            "Run: python src/decision_engine.py"
        )

    try:
        products = pd.read_csv(DATASET_FILE)
        decisions = pd.read_csv(DECISIONS_FILE)
    except (OSError, pd.errors.ParserError, UnicodeError) as error:
        raise ValueError(f"Could not read CSV input: {error}") from error

    missing_data = set(REQUIRED_DATA_COLUMNS) - set(products.columns)
    missing_decisions = set(REQUIRED_DECISION_COLUMNS) - set(decisions.columns)

    if missing_data:
        raise ValueError(f"Dataset missing columns: {sorted(missing_data)}")
    if missing_decisions:
        raise ValueError(
            f"Decisions missing columns: {sorted(missing_decisions)}"
        )
    if products.empty:
        raise ValueError("The construction dataset is empty.")
    if decisions.empty:
        raise ValueError("The decision dataset is empty.")

    for frame, label in [(products, "products"), (decisions, "decisions")]:
        if frame["product_id"].isna().any():
            raise ValueError(f"Missing product IDs in {label}.")
        frame["product_id"] = frame["product_id"].astype(str).str.strip()
        if frame["product_id"].eq("").any():
            raise ValueError(f"Empty product IDs in {label}.")
        if frame["product_id"].duplicated().any():
            raise ValueError(f"Duplicate product IDs in {label}.")

    for column in ["product_name", "category", "unit", "seasonality"]:
        products[column] = products[column].astype("string").str.strip()
        if products[column].isna().any() or products[column].eq("").any():
            raise ValueError(f"Missing or empty values in '{column}'.")

    for column in NUMERIC_COLUMNS:
        products[column] = pd.to_numeric(products[column], errors="coerce")

    if products[NUMERIC_COLUMNS].isna().any().any():
        raise ValueError("Missing or invalid numeric inventory values.")

    if not products[NUMERIC_COLUMNS].map(
        lambda value: math.isfinite(float(value))
    ).all().all():
        raise ValueError("Inventory values must be finite numbers.")

    if (products[NUMERIC_COLUMNS] < 0).any().any():
        raise ValueError("Negative inventory values are not allowed.")

    if (products["lead_time_days"] <= 0).any():
        raise ValueError("Lead time must be greater than zero.")

    decisions["decision_category"] = (
        decisions["decision_category"].astype("string").str.strip()
    )

    if decisions["decision_category"].isna().any():
        raise ValueError("Missing decision categories.")

    invalid = set(decisions["decision_category"].unique()) - VALID_STATUSES
    if invalid:
        raise ValueError(f"Invalid decision categories: {sorted(invalid)}")

    merged = products.merge(
        decisions[["product_id", "decision_category"]],
        on="product_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    missing_ids = merged.loc[merged["_merge"] != "both", "product_id"].tolist()
    if missing_ids:
        raise ValueError(f"Products missing decisions: {missing_ids}")

    # Do not silently ignore decision IDs that have no matching product.
    extra_ids = set(decisions["product_id"]) - set(products["product_id"])
    if extra_ids:
        raise ValueError(f"Decisions reference unknown products: {sorted(extra_ids)}")

    return merged.drop(columns=["_merge"])


def calculate_reorder_quantity(row, config):
    """
    Use the mentor formula with an optional seasonal safety-stock buffer.
    Reorder-level logic is also considered as an additional target threshold.
    """
    if row["decision_category"] not in REORDER_STATUSES:
        return 0

    current_stock = float(row["current_stock"])
    daily_sales = float(row["avg_daily_sales"])
    lead_time = float(row["lead_time_days"])
    safety_stock = float(row["safety_stock"])
    reorder_level = float(row["reorder_level"])

    seasonality = str(row["seasonality"]).strip().upper()
    if seasonality in {"HIGH", "SEASONAL", "YES", "TRUE"}:
        multiplier = config["seasonal_safety_multiplier"]
    else:
        multiplier = config["normal_safety_multiplier"]

    adjusted_safety_stock = math.ceil(safety_stock * multiplier)

    lead_time_demand = daily_sales * lead_time

    # Mentor formula baseline:
    mentor_target = lead_time_demand + adjusted_safety_stock

    # Extra business rule: do not recommend below the configured reorder target.
    target_stock = max(reorder_level, mentor_target)

    # Do not force a purchase if the target is already met.
    quantity = max(0, math.ceil(target_stock - current_stock))

    # A flagged product at target stock gets a minimum suggestion of 1 unit.
    if quantity == 0 and row["decision_category"] in REORDER_STATUSES:
        quantity = 1

    return int(quantity)


def create_reorder_reason(row):
    status = row["decision_category"]
    quantity = int(row["recommended_reorder_quantity"])
    days = row["days_of_stock_remaining"]

    if status == "URGENT REORDER":
        return (
            f"Stock is below the safety-stock level. "
            f"Review the suggested {quantity} {row['unit']} replenishment."
        )
    if status == "REORDER SOON":
        return (
            f"Stock has reached the reorder zone. "
            f"Suggested quantity: {quantity} {row['unit']}."
        )
    if status == "OVERSTOCK RISK":
        return (
            f"Stock may cover approximately {days:.1f} days of sales. "
            "Review future purchases before replenishing."
        )
    return "Stock is within the configured healthy range; no reorder is suggested."


def create_reorder_action(row):
    status = row["decision_category"]
    quantity = int(row["recommended_reorder_quantity"])
    unit = row["unit"]

    if status == "URGENT REORDER":
        return f"Prioritize human review of a {quantity} {unit} replenishment."
    if status == "REORDER SOON":
        return f"Plan and review a {quantity} {unit} replenishment soon."
    if status == "OVERSTOCK RISK":
        return "Review excess stock and pause unnecessary replenishment."
    return "Continue routine inventory monitoring."


def main():
    print("=" * 65)
    print("BUILDSTOCK AI - MODULE 5")
    print("REORDER QUANTITY RECOMMENDATION")
    print("=" * 65)

    df = load_and_validate_data()
    config = load_config()

    # Guard against division by zero when calculating days of stock.
    df["days_of_stock_remaining"] = df.apply(
        lambda row: (
            float(row["current_stock"]) / float(row["avg_daily_sales"])
            if float(row["avg_daily_sales"]) > 0
            else math.inf
        ),
        axis=1,
    )

    df["recommended_reorder_quantity"] = df.apply(
        lambda row: calculate_reorder_quantity(row, config),
        axis=1,
    ).astype(int)

    df["reorder_reason"] = df.apply(create_reorder_reason, axis=1)
    df["reorder_action"] = df.apply(create_reorder_action, axis=1)
    df["disclaimer"] = (
        "AI-generated planning suggestion only. "
        "Review actual demand, supplier pack sizes, budget, and stock "
        "before making purchasing decisions. No order is placed automatically."
    )

    if (df["recommended_reorder_quantity"] < 0).any():
        raise ValueError("Negative reorder quantities are not allowed.")

    flagged = df["decision_category"].isin(REORDER_STATUSES)
    if (df.loc[~flagged, "recommended_reorder_quantity"] != 0).any():
        raise ValueError("Non-reorder products must have zero reorder quantity.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    display_columns = [
        "product_id",
        "product_name",
        "decision_category",
        "days_of_stock_remaining",
        "recommended_reorder_quantity",
        "unit",
        "reorder_action",
    ]

    print("\nREORDER RECOMMENDATIONS")
    print("-" * 65)
    print(df[display_columns].to_string(index=False))

    print("\nProducts analyzed:", len(df))
    print(
        "Products needing replenishment:",
        int((df["recommended_reorder_quantity"] > 0).sum()),
    )
    print("Output saved to:", OUTPUT_FILE)
    print("\nAll recommendations require human review.")


if __name__ == "__main__":
    main()
