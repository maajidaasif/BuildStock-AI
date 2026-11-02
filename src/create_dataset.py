
"""
BuildStock AI - Module 1
Construction Inventory Dataset Management

Creates a synthetic inventory dataset with:
- 20 original construction products
- 1 stock-out edge case
- 1 overstock edge case
- Seasonal indicators

No real supplier or pricing data is used.
"""

from pathlib import Path
import pandas as pd


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = DATA_DIR / "construction_products.csv"


# --------------------------------------------------
# SYNTHETIC CONSTRUCTION INVENTORY DATA
# --------------------------------------------------

products = [
    {
        "product_id": "CP001",
        "product_name": "OPC 53 Grade Cement",
        "category": "Cement",
        "unit": "bags",
        "current_stock": 100,
        "avg_daily_sales": 15,
        "lead_time_days": 5,
        "safety_stock": 40,
        "reorder_level": 75,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP002",
        "product_name": "PPC Cement",
        "category": "Cement",
        "unit": "bags",
        "current_stock": 180,
        "avg_daily_sales": 12,
        "lead_time_days": 4,
        "safety_stock": 35,
        "reorder_level": 60,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP003",
        "product_name": "White Cement",
        "category": "Cement",
        "unit": "bags",
        "current_stock": 25,
        "avg_daily_sales": 3,
        "lead_time_days": 4,
        "safety_stock": 15,
        "reorder_level": 20,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP004",
        "product_name": "8mm TMT Steel Rods",
        "category": "Steel",
        "unit": "tons",
        "current_stock": 8,
        "avg_daily_sales": 1,
        "lead_time_days": 7,
        "safety_stock": 4,
        "reorder_level": 6,
        "seasonality": "High",
    },
    {
        "product_id": "CP005",
        "product_name": "10mm TMT Steel Rods",
        "category": "Steel",
        "unit": "tons",
        "current_stock": 12,
        "avg_daily_sales": 1.5,
        "lead_time_days": 6,
        "safety_stock": 5,
        "reorder_level": 8,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP006",
        "product_name": "12mm TMT Steel Rods",
        "category": "Steel",
        "unit": "tons",
        "current_stock": 3,
        "avg_daily_sales": 1,
        "lead_time_days": 8,
        "safety_stock": 5,
        "reorder_level": 7,
        "seasonality": "High",
    },
    {
        "product_id": "CP007",
        "product_name": "16mm TMT Steel Rods",
        "category": "Steel",
        "unit": "tons",
        "current_stock": 15,
        "avg_daily_sales": 1,
        "lead_time_days": 7,
        "safety_stock": 4,
        "reorder_level": 7,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP008",
        "product_name": "Binding Wire",
        "category": "Steel",
        "unit": "kg",
        "current_stock": 200,
        "avg_daily_sales": 20,
        "lead_time_days": 3,
        "safety_stock": 50,
        "reorder_level": 80,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP009",
        "product_name": "Red Clay Bricks",
        "category": "Bricks",
        "unit": "units",
        "current_stock": 5000,
        "avg_daily_sales": 500,
        "lead_time_days": 3,
        "safety_stock": 1000,
        "reorder_level": 1800,
        "seasonality": "High",
    },
    {
        "product_id": "CP010",
        "product_name": "Fly Ash Bricks",
        "category": "Bricks",
        "unit": "units",
        "current_stock": 2500,
        "avg_daily_sales": 250,
        "lead_time_days": 4,
        "safety_stock": 700,
        "reorder_level": 1200,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP011",
        "product_name": "AAC Blocks",
        "category": "Blocks",
        "unit": "units",
        "current_stock": 300,
        "avg_daily_sales": 40,
        "lead_time_days": 5,
        "safety_stock": 100,
        "reorder_level": 180,
        "seasonality": "High",
    },
    {
        "product_id": "CP012",
        "product_name": "M-Sand",
        "category": "Aggregates",
        "unit": "tons",
        "current_stock": 20,
        "avg_daily_sales": 5,
        "lead_time_days": 2,
        "safety_stock": 8,
        "reorder_level": 12,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP013",
        "product_name": "Blue Metal Gravel",
        "category": "Aggregates",
        "unit": "tons",
        "current_stock": 40,
        "avg_daily_sales": 3,
        "lead_time_days": 3,
        "safety_stock": 10,
        "reorder_level": 15,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP014",
        "product_name": "Exterior Primer",
        "category": "Paint",
        "unit": "litres",
        "current_stock": 80,
        "avg_daily_sales": 8,
        "lead_time_days": 4,
        "safety_stock": 25,
        "reorder_level": 40,
        "seasonality": "High",
    },
    {
        "product_id": "CP015",
        "product_name": "Weatherproof Exterior Paint",
        "category": "Paint",
        "unit": "litres",
        "current_stock": 15,
        "avg_daily_sales": 5,
        "lead_time_days": 5,
        "safety_stock": 20,
        "reorder_level": 30,
        "seasonality": "High",
    },
    {
        "product_id": "CP016",
        "product_name": "Wall Care Putty",
        "category": "Finishing",
        "unit": "kg",
        "current_stock": 600,
        "avg_daily_sales": 60,
        "lead_time_days": 4,
        "safety_stock": 150,
        "reorder_level": 250,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP017",
        "product_name": "Waterproofing Chemical",
        "category": "Chemicals",
        "unit": "litres",
        "current_stock": 50,
        "avg_daily_sales": 4,
        "lead_time_days": 5,
        "safety_stock": 15,
        "reorder_level": 25,
        "seasonality": "High",
    },
    {
        "product_id": "CP018",
        "product_name": "PVC Pipes",
        "category": "Plumbing",
        "unit": "units",
        "current_stock": 200,
        "avg_daily_sales": 15,
        "lead_time_days": 4,
        "safety_stock": 50,
        "reorder_level": 80,
        "seasonality": "Normal",
    },
    {
        "product_id": "CP019",
        "product_name": "CPVC Pipes",
        "category": "Plumbing",
        "unit": "units",
        "current_stock": 8,
        "avg_daily_sales": 5,
        "lead_time_days": 6,
        "safety_stock": 20,
        "reorder_level": 30,
        "seasonality": "High",
    },
    {
        "product_id": "CP020",
        "product_name": "PVC Pipe Solvent Cement",
        "category": "Plumbing",
        "unit": "cans",
        "current_stock": 150,
        "avg_daily_sales": 5,
        "lead_time_days": 3,
        "safety_stock": 20,
        "reorder_level": 40,
        "seasonality": "Normal",
    },

    # Edge case 1: Stock-out
    {
        "product_id": "CP021",
        "product_name": "Emergency Cement Stock",
        "category": "Cement",
        "unit": "bags",
        "current_stock": 0,
        "avg_daily_sales": 5,
        "lead_time_days": 6,
        "safety_stock": 20,
        "reorder_level": 40,
        "seasonality": "High",
    },

    # Edge case 2: Overstock
    {
        "product_id": "CP022",
        "product_name": "Excess Binding Wire Stock",
        "category": "Steel",
        "unit": "kg",
        "current_stock": 500,
        "avg_daily_sales": 2,
        "lead_time_days": 5,
        "safety_stock": 20,
        "reorder_level": 50,
        "seasonality": "Normal",
    },
]


# --------------------------------------------------
# DATASET CREATION
# --------------------------------------------------

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(products)

    required_columns = [
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

    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Dataset is missing columns: {sorted(missing_columns)}"
        )

    if df["product_id"].duplicated().any():
        raise ValueError("Duplicate product IDs found.")

    numeric_columns = [
        "current_stock",
        "avg_daily_sales",
        "lead_time_days",
        "safety_stock",
        "reorder_level",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="raise")

        if df[column].isna().any():
            raise ValueError(f"Missing numeric values in {column}.")

        if (df[column] < 0).any():
            raise ValueError(f"Negative values found in {column}.")

    if (df["lead_time_days"] <= 0).any():
        raise ValueError("Lead time must be greater than zero.")

    if df[required_columns].isna().any().any():
        raise ValueError("Missing required values found in dataset.")

    df.to_csv(OUTPUT_FILE, index=False)

    print("=" * 60)
    print("BUILDSTOCK AI - MODULE 1")
    print("CONSTRUCTION INVENTORY DATASET")
    print("=" * 60)
    print(f"Total products created: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"Dataset saved to: {OUTPUT_FILE}")

    print("\nProduct count by category:")
    print(df["category"].value_counts().to_string())

    print("\nSeasonality distribution:")
    print(df["seasonality"].value_counts().to_string())

    print("\nEdge-case products:")
    print(
        df[df["product_id"].isin(["CP021", "CP022"])][
            ["product_id", "product_name", "current_stock",
             "avg_daily_sales", "seasonality"]
        ].to_string(index=False)
    )

    print("\nFirst 5 products:")
    print(df.head().to_string(index=False))

    print("\nModule 1 dataset creation completed successfully!")


if __name__ == "__main__":
    main()
