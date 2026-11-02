
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
    "product_id", "product_name", "category", "unit",
    "current_stock", "avg_daily_sales", "lead_time_days",
    "safety_stock", "reorder_level", "seasonality",
]

REQUIRED_DECISION_COLUMNS = ["product_id", "decision_category"]

REORDER_STATUSES = {"URGENT REORDER", "REORDER SOON"}

NO_SALES_STATUS = "NO SALES - REVIEW REQUIRED"

VALID_STATUSES = REORDER_STATUSES | {
    "OVERSTOCK RISK",
    "STOCK HEALTHY",
    NO_SALES_STATUS,
}

NUMERIC_COLUMNS = [
    "current_stock",
    "avg_daily_sales",
    "lead_time_days",
    "safety_stock",
    "reorder_level",
]


def load_config():
    """Load inventory configuration with safe defaults."""

    config = {
        "seasonal_safety_multiplier": 1.2,
        "normal_safety_multiplier": 1.0,
    }

    if not CONFIG_FILE.exists():
        return config

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            supplied = json.load(file)

        if not isinstance(supplied, dict):
            raise ValueError("Configuration must be a JSON object.")

    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(
            f"Invalid inventory rules JSON: {error}"
        ) from error

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
    """Load and validate product and decision CSV files."""

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

    if products.empty or decisions.empty:
        raise ValueError("Product or decision dataset is empty.")

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

    missing_ids = merged.loc[
        merged["_merge"] != "both", "product_id"
    ].tolist()

    if missing_ids:
        raise ValueError(f"Products missing decisions: {missing_ids}")

    extra_ids = set(decisions["product_id"]) - set(products["product_id"])

    if extra_ids:
        raise ValueError(
            f"Decisions reference unknown products: {sorted(extra_ids)}"
        )

    merged = merged.drop(columns=["_merge"])

    # Verify that zero-sales products have the correct decision status.
    zero_sales = merged["avg_daily_sales"] == 0
    no_sales_status = merged["decision_category"] == NO_SALES_STATUS

    if (zero_sales != no_sales_status).any():
        raise ValueError(
            "Sales and decision status mismatch. "
            "Products with zero daily sales must have "
            "'NO SALES - REVIEW REQUIRED'. "
            "Run Module 4 again."
        )

    return merged


def calculate_reorder_quantity(row, config):
    """Calculate advisory replenishment quantity."""

    status = row["decision_category"]

    # No-sales and non-reorder products must not receive quantities.
    if status not in REORDER_STATUSES:
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

    mentor_target = lead_time_demand + adjusted_safety_stock
    target_stock = max(reorder_level, mentor_target)

    quantity = max(0, math.ceil(target_stock - current_stock))

    # Minimum suggestion for a flagged reorder product.
    if quantity == 0:
        quantity = 1

    return int(quantity)


def calculate_days_of_stock(row):
    """Return stock coverage, or None when sales are zero."""

    daily_sales = float(row["avg_daily_sales"])

    if daily_sales <= 0:
        return None

    return float(row["current_stock"]) / daily_sales


def create_reorder_reason(row):
    status = row["decision_category"]
    quantity = int(row["recommended_reorder_quantity"])
    days = row["days_of_stock_remaining"]

    if status == "URGENT REORDER":
        return (
            "Stock is below the safety-stock level. "
            f"Review the suggested {quantity} {row['unit']} replenishment."
        )

    if status == "REORDER SOON":
        return (
            "Stock has reached the reorder zone. "
            f"Suggested quantity: {quantity} {row['unit']}."
        )

    if status == "OVERSTOCK RISK":
        if pd.notna(days):
            return (
                f"Stock may cover approximately {days:.1f} days of sales. "
                "Review future purchases before replenishing."
            )

        return "Review excess stock and future purchasing plans."

    if status == NO_SALES_STATUS:
        return (
            "No daily sales have been recorded. "
            "Review product demand and sales history before "
            "making any replenishment decision."
        )

    return (
        "Stock is within the configured healthy range; "
        "no reorder is suggested."
    )


def create_reorder_action(row):
    status = row["decision_category"]
    quantity = int(row["recommended_reorder_quantity"])
    unit = row["unit"]

    if status == "URGENT REORDER":
        return (
            f"Prioritize human review of a {quantity} {unit} replenishment."
        )

    if status == "REORDER SOON":
        return f"Plan and review a {quantity} {unit} replenishment soon."

    if status == "OVERSTOCK RISK":
        return "Review excess stock and pause unnecessary replenishment."

    if status == NO_SALES_STATUS:
        return (
            "Manually review product demand and stock. "
            "Do not reorder automatically."
        )

    return "Continue routine inventory monitoring."


def main():
    print("=" * 65)
    print("BUILDSTOCK AI - MODULE 5")
    print("REORDER QUANTITY RECOMMENDATION")
    print("=" * 65)

    df = load_and_validate_data()
    config = load_config()

    df["days_of_stock_remaining"] = df.apply(
        calculate_days_of_stock,
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
        raise ValueError(
            "Non-reorder products must have zero reorder quantity."
        )

    no_sales = df["decision_category"] == NO_SALES_STATUS

    if (df.loc[no_sales, "recommended_reorder_quantity"] != 0).any():
        raise ValueError(
            "No-sales products must have zero reorder quantity."
        )

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
    print(
        "Products requiring no-sales review:",
        int(no_sales.sum()),
    )

    print("Output saved to:", OUTPUT_FILE)
    print("\nAll recommendations require human review.")


if __name__ == "__main__":
    main()
