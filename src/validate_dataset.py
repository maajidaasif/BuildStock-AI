
import pandas as pd
from pathlib import Path

# BuildStock AI - Module 2
# Data Input and Validation

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "construction_products.csv"

REQUIRED_COLUMNS = [
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

NUMERIC_COLUMNS = [
    "current_stock",
    "avg_daily_sales",
    "lead_time_days",
    "safety_stock",
    "reorder_level",
]


def validate_dataset():
    print("=" * 55)
    print("BUILDSTOCK AI - MODULE 2")
    print("DATA INPUT AND VALIDATION")
    print("=" * 55)

    # 1. Check whether the CSV file exists
    if not DATA_FILE.exists():
        print(f"ERROR: Dataset file not found: {DATA_FILE}")
        return

    # 2. Read the CSV file
    try:
        df = pd.read_csv(DATA_FILE)
    except (OSError, pd.errors.ParserError, UnicodeError) as error:
        print(f"ERROR: Unable to read CSV: {error}")
        return

    print(f"\nDataset loaded: {DATA_FILE.name}")
    print(f"Rows found: {len(df)}")
    print(f"Columns found: {len(df.columns)}")

    errors = []
    warnings = []

    # 3. Check required columns
    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        errors.append(
            f"Missing required columns: {missing_columns}"
        )

    # Further checks require all expected columns
    if missing_columns:
        print("\nVALIDATION ERRORS:")
        for error in errors:
            print(f"- {error}")

        print("\nDataset validation FAILED.")
        return

    # 4. Check missing values
    for column in REQUIRED_COLUMNS:
        missing_count = int(df[column].isna().sum())

        if missing_count > 0:
            errors.append(
                f"{column}: {missing_count} missing value(s)"
            )

    # 5. Check duplicate product IDs
    duplicate_ids = df["product_id"].duplicated(keep=False)

    if duplicate_ids.any():
        ids = df.loc[duplicate_ids, "product_id"].tolist()
        errors.append(f"Duplicate product IDs: {ids}")

    # 6. Check empty text fields
    text_columns = [
        "product_id",
        "product_name",
        "category",
        "unit",
        "seasonality",
    ]

    for column in text_columns:
        empty_mask = (
            df[column].astype("string").str.strip().eq("").fillna(False)
        )

        if empty_mask.any():
            errors.append(
                f"{column}: {int(empty_mask.sum())} empty value(s)"
            )

    # 7. Convert numeric fields and validate values
    for column in NUMERIC_COLUMNS:
        original = df[column]
        converted = pd.to_numeric(original, errors="coerce")

        invalid_mask = original.notna() & converted.isna()

        if invalid_mask.any():
            errors.append(
                f"{column}: {int(invalid_mask.sum())} non-numeric value(s)"
            )

        df[column] = converted

    # Stop numeric comparisons if values cannot be converted
    if not any("non-numeric value" in error for error in errors):

        for column in NUMERIC_COLUMNS:
            if (df[column] < 0).any():
                errors.append(
                    f"{column}: negative values are not allowed"
                )

        if (df["lead_time_days"] % 1 != 0).any():
            errors.append(
                "lead_time_days: values must be whole days"
            )

        if (df["lead_time_days"] < 1).any():
            errors.append(
                "lead_time_days: must be at least 1 day"
            )

        # 8. Check allowed seasonality values
        allowed_seasonality = {"Normal", "High"}

        actual_seasonality = (
            df["seasonality"]
            .astype("string")
            .str.strip()
            .str.title()
        )

        invalid_seasonality = (
            ~actual_seasonality.isin(allowed_seasonality)
        )

        if invalid_seasonality.any():
            errors.append(
                "seasonality: values must be High or Normal"
            )

        # 9. Check inventory relationships
        if (
            df["reorder_level"] < df["safety_stock"]
        ).any():
            warnings.append(
                "Some reorder levels are below safety stock."
            )

        if (
            df["avg_daily_sales"] == 0
        ).any():
            warnings.append(
                "Some products have zero daily sales."
            )

    # 10. Print validation report
    print("\nVALIDATION REPORT")
    print("-" * 55)

    if errors:
        print("Status: FAILED")

        for error in errors:
            print(f"[ERROR] {error}")
    else:
        print("Status: PASSED")
        print("All required columns are present.")
        print("No missing or duplicate product IDs found.")
        print("Numeric values passed validation.")

    if warnings:
        print("\nWARNINGS:")

        for warning in warnings:
            print(f"[WARNING] {warning}")

    if not errors:
        print("\nDataset summary:")
        print(f"Valid products: {len(df)}")
        print(
            "Categories:",
            df["category"].nunique()
        )
        print(
            "Total current stock values:",
            df["current_stock"].sum()
        )
        print("\nModule 2 validation completed successfully.")
    else:
        print("\nPlease correct the errors before proceeding.")


if __name__ == "__main__":
    validate_dataset()
