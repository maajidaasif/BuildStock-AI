
import math
import re
import numpy as np
import pandas as pd
import requests
from pathlib import Path

# ============================================================
# BUILDSTOCK AI - MODULE 6
# Product-Specific Local LLM Inventory Explanation
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DECISIONS_FILE = ROOT / "data" / "inventory_decisions.csv"
RECOMMENDATIONS_FILE = ROOT / "data" / "reorder_recommendations.csv"
OUTPUT_FILE = ROOT / "data" / "ai_inventory_explanations.csv"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

TIMEOUT_SECONDS = 180
MAX_EXPLANATION_WORDS = 65

VALID_STATUSES = {
    "URGENT REORDER",
    "REORDER SOON",
    "OVERSTOCK RISK",
    "STOCK HEALTHY",
    "NO SALES - REVIEW REQUIRED",
}

NUMBER_WORDS = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundred|thousand|million|first|second|third)\b",
    re.IGNORECASE,
)


# ============================================================
# MODULE 6 - FILE VALIDATION
# ============================================================

def validate_files():
    """Check whether the required input files exist."""

    required_files = [
        DECISIONS_FILE,
        RECOMMENDATIONS_FILE,
    ]

    for file_path in required_files:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}. "
                "Run Modules 4 and 5 first."
            )

    return True


# ============================================================
# MODULE 6 - LOAD AND VALIDATE INVENTORY DATA
# ============================================================

def load_inventory_data():
    """Load rule-engine decisions and reorder recommendations."""

    decisions = pd.read_csv(DECISIONS_FILE)
    recommendations = pd.read_csv(RECOMMENDATIONS_FILE)

    required_decision_columns = [
        "product_id",
        "product_name",
        "current_stock",
        "avg_daily_sales",
        "lead_time_days",
        "safety_stock",
        "decision_category",
        "decision_reason",
        "unit",
    ]

    required_recommendation_columns = [
        "product_id",
        "recommended_reorder_quantity",
    ]

    for column in required_decision_columns:
        if column not in decisions.columns:
            raise ValueError(
                f"Missing column in decisions file: {column}"
            )

    for column in required_recommendation_columns:
        if column not in recommendations.columns:
            raise ValueError(
                f"Missing column in recommendations file: {column}"
            )

    if decisions.empty or recommendations.empty:
        raise ValueError("An input inventory file is empty.")

    for name, data in [
        ("decisions", decisions),
        ("recommendations", recommendations),
    ]:
        data["product_id"] = (
            data["product_id"].astype("string").str.strip()
        )

        if (
            data["product_id"].isna().any()
            or data["product_id"].eq("").any()
        ):
            raise ValueError(f"Missing product IDs in {name} file.")

        if data["product_id"].duplicated().any():
            raise ValueError(f"Duplicate product IDs in {name} file.")

    df = decisions.merge(
        recommendations[
            ["product_id", "recommended_reorder_quantity"]
        ],
        on="product_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    if (df["_merge"] != "both").any():
        missing_ids = df.loc[
            df["_merge"] != "both", "product_id"
        ].tolist()

        raise ValueError(
            f"Missing recommendations for products: {missing_ids}"
        )

    df.drop(columns=["_merge"], inplace=True)

    extra_ids = (
        set(recommendations["product_id"])
        - set(decisions["product_id"])
    )

    if extra_ids:
        raise ValueError(
            f"Unknown product IDs in recommendations: {sorted(extra_ids)}"
        )

    numeric_columns = [
        "current_stock",
        "avg_daily_sales",
        "lead_time_days",
        "safety_stock",
        "recommended_reorder_quantity",
    ]

    optional_numeric_columns = [
        "adjusted_safety_stock",
        "lead_time_demand",
        "effective_reorder_level",
    ]

    for column in optional_numeric_columns:
        if column in df.columns:
            numeric_columns.append(column)

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    values = df[numeric_columns].to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError(
            "Inventory data contains missing, invalid, "
            "or infinite numeric values."
        )

    if (df[numeric_columns] < 0).any().any():
        raise ValueError("Negative inventory values are not permitted.")

    if (df["lead_time_days"] < 1).any():
        raise ValueError("Lead time must be at least one day.")

    for column in ["product_name", "unit"]:
        if df[column].isna().any():
            raise ValueError(f"Missing {column} values.")

        df[column] = df[column].astype(str).str.strip()

        if df[column].eq("").any():
            raise ValueError(f"Empty {column} values.")

    if df["decision_category"].isna().any():
        raise ValueError("Missing decision categories.")

    df["decision_category"] = (
        df["decision_category"].astype(str).str.strip()
    )

    invalid_statuses = (
        set(df["decision_category"]) - VALID_STATUSES
    )

    if invalid_statuses:
        raise ValueError(
            f"Unknown inventory statuses: {sorted(invalid_statuses)}"
        )

    df["decision_reason"] = (
        df["decision_reason"].fillna("").astype(str).str.strip()
    )

    needs_reorder = df["decision_category"].isin(
        ["URGENT REORDER", "REORDER SOON"]
    )

    if (
        df.loc[needs_reorder, "recommended_reorder_quantity"] <= 0
    ).any():
        raise ValueError(
            "A reorder status has a zero or negative recommendation."
        )

    no_reorder = df["decision_category"].isin(
        [
            "STOCK HEALTHY",
            "OVERSTOCK RISK",
            "NO SALES - REVIEW REQUIRED",
        ]
    )

    if (
        df.loc[no_reorder, "recommended_reorder_quantity"] != 0
    ).any():
        raise ValueError(
            "Healthy, overstock, and no-sales products "
            "must have zero reorder quantity."
        )

    # Check consistency between zero sales and the new status.
    zero_sales = df["avg_daily_sales"] == 0
    no_sales_status = (
        df["decision_category"] == "NO SALES - REVIEW REQUIRED"
    )

    if (zero_sales != no_sales_status).any():
        raise ValueError(
            "Zero-sales data and inventory decision status do not match. "
            "Run Module 4 again."
        )

    return df


# ============================================================
# MODULE 6 - VERIFIED FACTS
# ============================================================

def format_number(value):
    """Format numbers without unnecessary decimal zeros."""

    number = float(value)

    if not math.isfinite(number):
        raise ValueError("Cannot format a non-finite number.")

    if number.is_integer():
        return str(int(number))

    return f"{number:.2f}".rstrip("0").rstrip(".")


def get_optional_fact(row, column):
    """Return an optional calculated value if available."""

    if column not in row.index:
        return None

    value = row[column]

    if pd.isna(value):
        return None

    return format_number(value)


def build_verified_facts(row):
    """Build numerical facts using rule-engine output only."""

    unit = row["unit"]

    facts = [
        f"Product: {row['product_name']}",
        f"Product ID: {row['product_id']}",
        f"Unit: {unit}",
        f"Current stock: {format_number(row['current_stock'])} {unit}",
        (
            f"Average daily sales: "
            f"{format_number(row['avg_daily_sales'])} {unit} per day"
        ),
        f"Lead time: {format_number(row['lead_time_days'])} days",
        f"Safety stock: {format_number(row['safety_stock'])} {unit}",
        f"Inventory status: {row['decision_category']}",
        f"Rule-based reason: {row['decision_reason']}",
        (
            f"Recommended reorder quantity: "
            f"{format_number(row['recommended_reorder_quantity'])} {unit}"
        ),
    ]

    calculated_fields = {
        "adjusted_safety_stock": "Adjusted safety stock",
        "lead_time_demand": "Lead-time demand",
        "effective_reorder_level": "Effective reorder level",
    }

    for column, label in calculated_fields.items():
        value = get_optional_fact(row, column)

        if value is not None:
            facts.append(f"{label}: {value} {unit}")

    return "\n".join(facts)


# ============================================================
# MODULE 6 - PRODUCT-SPECIFIC LLM PROMPT
# ============================================================

def create_prompt(row):
    """Generate a product-specific explanation."""

    product_name = row["product_name"]
    status = row["decision_category"]
    reason = row["decision_reason"]

    if status == "NO SALES - REVIEW REQUIRED":
        special_instruction = (
            "Explain that no daily sales are recorded and manual "
            "demand review is required. Do not recommend replenishment."
        )
    else:
        special_instruction = (
            "Explain the supplied inventory status and the rule-based reason."
        )

    return f"""
You are BuildStock AI, an inventory explanation assistant.

Use ONLY the verified inventory facts below.

VERIFIED INVENTORY FACTS:
{build_verified_facts(row)}

YOUR TASK:
Write one clear, product-specific explanation in simple English.

STRICT RULES:
1. Mention the exact product name: {product_name}.
2. Explain the supplied inventory status: {status}.
3. Use the supplied rule-based reason: {reason}.
4. Mention numerical facts only when they match verified facts.
5. Never invent quantities, sales, lead times or reorder values.
6. Do not invent causes or sales trends.
7. Do not change or contradict the inventory status.
8. Do not claim that an order has been placed.
9. Do not give purchasing instructions.
10. Keep the explanation specific to this product.
11. Use simple English and one sentence.
12. Maximum {MAX_EXPLANATION_WORDS} words.
13. Do not calculate stock-duration estimates.
14. {special_instruction}

Write only the explanation.
""".strip()


# ============================================================
# MODULE 6 - OLLAMA CONNECTIVITY
# ============================================================

def check_ollama():
    """Confirm Ollama is running and the model is installed."""

    tags_url = "http://localhost:11434/api/tags"

    response = requests.get(tags_url, timeout=10)
    response.raise_for_status()

    models = response.json().get("models", [])

    installed_models = [
        model.get("name", "") for model in models
    ]

    matching_model = any(
        name == MODEL_NAME
        or name.startswith(MODEL_NAME + ":")
        for name in installed_models
    )

    if not matching_model:
        raise RuntimeError(
            f"Model '{MODEL_NAME}' is not installed. "
            f"Available models: {installed_models}"
        )

    print("Ollama connection: OK")
    print(f"Local model: {MODEL_NAME}")


# ============================================================
# MODULE 6 - CLEAN LLM RESPONSE
# ============================================================

def clean_explanation(text):
    """Clean common formatting artifacts."""

    text = str(text).strip()

    text = (
        text.replace("**", "")
        .replace("__", "")
        .replace("*", "")
    )

    text = re.sub(r"(?m)^\s*\d+[.)]\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    words = text.split()

    if len(words) > MAX_EXPLANATION_WORDS:
        text = " ".join(words[:MAX_EXPLANATION_WORDS])

    return text


# ============================================================
# MODULE 6 - NUMERICAL FACT VALIDATION
# ============================================================

def normalize_number(value):
    """Normalize numerical values for comparison."""

    try:
        number = float(value)

        if not math.isfinite(number):
            return None

        return round(number, 6)

    except (ValueError, TypeError):
        return None


def get_allowed_numbers(row):
    """Collect verified numerical values."""

    allowed = set()

    numeric_columns = [
        "current_stock",
        "avg_daily_sales",
        "lead_time_days",
        "safety_stock",
        "recommended_reorder_quantity",
        "adjusted_safety_stock",
        "lead_time_demand",
        "effective_reorder_level",
    ]

    for column in numeric_columns:
        if column not in row.index:
            continue

        value = row[column]

        if pd.isna(value):
            continue

        normalized = normalize_number(value)

        if normalized is not None:
            allowed.add(normalized)

    return allowed


def validate_numerical_claims(text, row):
    """Reject unsupported numerical values."""

    product_name = str(row["product_name"]).strip()

    text_without_product = re.sub(
        re.escape(product_name),
        "",
        text,
        flags=re.IGNORECASE,
    )

    allowed_numbers = get_allowed_numbers(row)

    found_numbers = re.findall(
        r"(?<![A-Za-z])\d+(?:\.\d+)?",
        text_without_product,
    )

    for value in found_numbers:
        normalized = normalize_number(value)

        if normalized not in allowed_numbers:
            return False, (
                f"Unsupported numerical claim detected: {value}"
            )

    if NUMBER_WORDS.search(text_without_product):
        return False, "Explanation contains unsupported number words"

    return True, "Numerical claims match verified inventory facts"


# ============================================================
# MODULE 6 - STATUS VALIDATION
# ============================================================

def validate_status(text, status):
    """Check whether the explanation agrees with the rule engine."""

    lower_text = text.lower()

    if status == "URGENT REORDER":

        valid_phrases = [
            "urgent reorder",
            "urgently need",
            "urgently needs",
            "critical stock",
            "critical stock condition",
            "urgent replenishment",
        ]

        contradictions = [
            "stock healthy",
            "no reorder needed",
            "overstock risk",
            "healthy inventory",
        ]

    elif status == "REORDER SOON":

        valid_phrases = [
            "reorder soon",
            "replenishment",
            "needs replenishment",
            "plan replenishment",
            "requires replenishment",
            "reorder level",
            "reorder threshold",
            "inventory is at risk",
        ]

        contradictions = [
            "stock healthy",
            "no reorder needed",
            "overstock risk",
            "healthy inventory",
        ]

    elif status == "OVERSTOCK RISK":

        valid_phrases = [
            "overstock risk",
            "overstock",
            "excess stock",
            "too much stock",
            "excess inventory",
            "excessive inventory",
        ]

        contradictions = [
            "urgent reorder",
            "reorder soon",
            "stock shortage",
            "stockout",
            "needs replenishment",
        ]

    elif status == "NO SALES - REVIEW REQUIRED":

        valid_phrases = [
            "no sales",
            "no recorded sales",
            "no daily sales",
            "manual review",
            "review required",
            "demand review",
            "sales are not recorded",
        ]

        contradictions = [
            "urgent reorder",
            "reorder soon",
            "stock healthy",
            "overstock risk",
            "needs replenishment",
            "place an order",
        ]

    else:  # STOCK HEALTHY

        valid_phrases = [
            "stock healthy",
            "healthy inventory",
            "inventory is healthy",
            "inventory remains healthy",
            "enough stock",
            "sufficient stock",
            "no need to reorder",
            "no need to order",
        ]

        contradictions = [
            "urgent reorder",
            "reorder soon",
            "overstock risk",
            "stock shortage",
            "stockout",
            "critically low",
        ]

    if any(phrase in lower_text for phrase in contradictions):
        return False, "Explanation contradicts the rule-based status"

    if not any(phrase in lower_text for phrase in valid_phrases):
        return False, (
            "Explanation does not clearly describe the correct status"
        )

    return True, "Inventory status verified"


# ============================================================
# MODULE 6 - VALIDATE LLM RESPONSE
# ============================================================

def validate_qualitative_response(text, row):
    """Validate product name, numerical facts and inventory status."""

    if not text:
        return False, "Empty LLM response"

    product_name = str(row["product_name"]).strip()

    if product_name.lower() not in text.lower():
        return False, "Explanation does not mention the product name"

    numbers_valid, number_reason = validate_numerical_claims(
        text,
        row,
    )

    if not numbers_valid:
        return False, number_reason

    status_valid, status_reason = validate_status(
        text,
        row["decision_category"],
    )

    if not status_valid:
        return False, status_reason

    return True, (
        "Passed product-specific, numerical and status validation"
    )


# ============================================================
# MODULE 6 - GENERATE LOCAL AI EXPLANATION
# ============================================================

def generate_ai_explanation(prompt, row):
    """Generate and validate an Ollama response."""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 120,
            },
        },
        timeout=TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    result = response.json()

    explanation = clean_explanation(
        result.get("response", "")
    )

    print(
        f"DEBUG - AI Response: {explanation}",
        flush=True,
    )

    is_valid, reason = validate_qualitative_response(
        explanation,
        row,
    )

    if not is_valid:
        raise ValueError(reason)

    return explanation


# ============================================================
# MODULE 6 - DETERMINISTIC FALLBACK EXPLANATION
# ============================================================

def create_fallback_explanation(row):
    """Create an explanation using verified rule-engine facts."""

    product_name = row["product_name"]
    unit = row["unit"]
    stock = format_number(row["current_stock"])
    quantity = format_number(
        row["recommended_reorder_quantity"]
    )

    status = row["decision_category"]
    reason = row["decision_reason"]

    if status == "URGENT REORDER":

        status_text = (
            f"{product_name} requires urgent inventory attention "
            "because the rule engine identifies a critical stock condition."
        )

    elif status == "REORDER SOON":

        status_text = (
            f"{product_name} requires planned replenishment "
            "according to the inventory rules."
        )

    elif status == "OVERSTOCK RISK":

        status_text = (
            f"{product_name} has an overstock risk. "
            "Review upcoming demand before replenishing."
        )

    elif status == "NO SALES - REVIEW REQUIRED":

        status_text = (
            f"{product_name} has no recorded daily sales. "
            "Manual review is required to understand product demand "
            "before making replenishment decisions."
        )

    else:

        status_text = (
            f"{product_name} currently has healthy inventory "
            "according to the rule engine."
        )

    if status == "NO SALES - REVIEW REQUIRED":

        recommendation = (
            "No reorder is recommended until sales and demand "
            "are manually reviewed."
        )

    elif float(row["recommended_reorder_quantity"]) > 0:

        recommendation = (
            f"The rule-based suggested reorder quantity is "
            f"{quantity} {unit}."
        )

    else:

        recommendation = (
            "The current rules do not recommend additional stock."
        )

    parts = [
        f"{product_name} currently has {stock} {unit} in stock.",
        f"Inventory status: {status}.",
    ]

    if reason:
        parts.append(f"Rule-based reason: {reason}")

    parts.extend([
        status_text,
        recommendation,
        "A human must review and approve any purchasing decision.",
    ])

    return " ".join(parts)


# ============================================================
# MODULE 6 - MAIN PIPELINE
# ============================================================

def run_ai_explanation():

    print("=" * 65)
    print("BUILDSTOCK AI - MODULE 6")
    print("PRODUCT-SPECIFIC LOCAL AI INVENTORY EXPLANATION")
    print("=" * 65)

    try:

        validate_files()

        df = load_inventory_data()

        check_ollama()

        explanations = []
        explanation_sources = []
        validation_notes = []

        total_products = len(df)
        fallback_count = 0

        for index, row in df.iterrows():

            print(
                f"\n[{index + 1}/{total_products}] "
                f"Analyzing: {row['product_name']}",
                flush=True,
            )

            try:

                prompt = create_prompt(row)

                qualitative_text = generate_ai_explanation(
                    prompt,
                    row,
                )

                verified_explanation = (
                    f"{build_verified_facts(row)}\n\n"
                    f"AI explanation: {qualitative_text}\n\n"
                    "A human must review and approve any purchasing decision."
                )

                explanations.append(verified_explanation)
                explanation_sources.append("Ollama LLM")

                validation_notes.append(
                    "Product-specific response passed numerical "
                    "and status validation"
                )

                print("AI explanation accepted.", flush=True)

            except (
                requests.exceptions.RequestException,
                ValueError,
                KeyError,
            ) as error:

                fallback_count += 1

                fallback_explanation = create_fallback_explanation(row)

                explanations.append(fallback_explanation)
                explanation_sources.append("Rule-based fallback")

                validation_notes.append(
                    f"Fallback used: {str(error)}"
                )

                print(
                    f"WARNING: AI response rejected or unavailable: {error}",
                    flush=True,
                )

                print(
                    "Using product-specific rule-based fallback.",
                    flush=True,
                )

        df["ai_explanation"] = explanations
        df["explanation_source"] = explanation_sources
        df["explanation_validation_note"] = validation_notes

        df.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8",
        )

        llm_count = sum(
            source == "Ollama LLM"
            for source in explanation_sources
        )

        print("\n" + "=" * 65)
        print("MODULE 6 FINISHED")
        print(f"Products processed: {total_products}")
        print(f"Accepted LLM explanations: {llm_count}")
        print(f"Rule-based fallbacks: {fallback_count}")
        print(f"Output saved to: {OUTPUT_FILE}")
        print("=" * 65)

        print(
            "Inventory decisions and reorder quantities remain rule-based."
        )

        print(
            "Numerical claims are checked against available "
            "verified inventory facts."
        )

        print(
            "Automated validation does not guarantee perfect "
            "factual accuracy."
        )

        print("Human approval is required before any purchase.")

    except requests.exceptions.ConnectionError:

        print("\nERROR: Cannot connect to Ollama.")
        print("Make sure Ollama is running at localhost:11434.")
        print("No new explanation file was generated.")

    except requests.exceptions.Timeout:

        print("\nERROR: Ollama request timed out.")
        print("No new explanation file was generated.")

    except requests.exceptions.RequestException as error:

        print(f"\nERROR: Ollama API request failed: {error}")

    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        pd.errors.ParserError,
    ) as error:

        print(f"\nERROR: {error}")


if __name__ == "__main__":
    run_ai_explanation()
