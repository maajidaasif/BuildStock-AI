# BuildStock AI – Construction Inventory Optimization AI Agent

BuildStock AI is an AI-powered inventory optimization system designed for construction materials. It analyzes inventory levels, daily sales, lead times, and safety stock to identify inventory risks and generate explainable replenishment recommendations.

The system combines a **rule-based decision engine** with a **locally running Large Language Model (LLM)** to support inventory management decisions.

All recommendations are advisory. Purchasing decisions require human review and approval.

## Key Features

- **Inventory Data Validation:** Validates product records, required columns, missing values, duplicate IDs, and numeric fields.
- **Inventory Analysis:** Calculates days of stock remaining, lead-time demand, and stock-level indicators.
- **Rule-Based Decision Engine:** Classifies products into four inventory categories:
  - URGENT REORDER
  - REORDER SOON
  - STOCK HEALTHY
  - OVERSTOCK RISK
- **Reorder Recommendations:** Calculates suggested replenishment quantities using inventory requirements.
- **Local AI Explanations:** Uses Ollama with Qwen2.5 3B to generate product-specific inventory explanations.
- **AI Explanation Validation:** Checks explanation structure and consistency with inventory data.
- **Inventory Alerts:** Assigns priorities to inventory risks:
  - P1 – Critical
  - P2 – High
  - P3 – Review
  - P4 – Normal
- **Interactive Dashboard:** Displays inventory summaries, product details, AI explanations, and alerts.
- **CSV Export:** Allows users to export inventory reports and recommendations.
- **System Testing:** Includes automated data-quality and cross-module consistency checks.

## System Architecture

```text
Construction Inventory Dataset
             |
             v
     Dataset Validation
             |
             v
      Inventory Analysis
             |
             v
    Rule-Based Decision Engine
             |
             v
   Reorder Recommendations
             |
             v
      Local AI Explanation
       (Ollama + Qwen2.5)
             |
             v
   AI Explanation Validation
             |
             v
    Inventory Alerts & Risks
             |
             v
     Streamlit Dashboard
             |
             v
      Human Review
```

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.11 |
| Data Processing | Pandas |
| Dashboard | Streamlit |
| Local LLM Runtime | Ollama |
| AI Model | Qwen2.5 3B |
| Data Storage | CSV |
| Configuration | JSON |
| Testing | Python |
| Version Control | Git and GitHub |

## Project Structure

```text
BuildStock-AI/
│
├── config/
│   └── inventory_rules.json
│
├── data/
│   ├── construction_products.csv
│   ├── inventory_analysis.csv
│   ├── inventory_decisions.csv
│   ├── reorder_recommendations.csv
│   ├── ai_inventory_explanations.csv
│   ├── inventory_alerts.csv
│   ├── analysis_history.csv
│   └── ai_explanation_validation.csv
│
├── src/
│   ├── create_dataset.py
│   ├── validate_dataset.py
│   ├── analyze_inventory.py
│   ├── decision_engine.py
│   ├── reorder_recommendation.py
│   ├── ai_inventory_explanation.py
│   ├── inventory_alerts.py
│   ├── dashboard.py
│   ├── system_tests.py
│   └── validate_ai_explanations.py
│
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/maajidaasif/BuildStock-AI.git
cd BuildStock-AI
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows:

```powershell
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Install and start Ollama

Install Ollama and download the required model:

```bash
ollama pull qwen2.5:3b
```

Ensure Ollama is running before executing the AI explanation module.

## Running the Project

Execute the modules in the following order:

```bash
python src/validate_dataset.py
python src/analyze_inventory.py
python src/decision_engine.py
python src/reorder_recommendation.py
python src/ai_inventory_explanation.py
python src/inventory_alerts.py
python src/validate_ai_explanations.py
python src/system_tests.py
```

### Launch the Dashboard

```bash
streamlit run src/dashboard.py
```

The Streamlit dashboard will open in your browser.

## Inventory Decision Logic

The system evaluates inventory using current stock, average daily sales, lead time, safety stock, reorder level, and configurable seasonal adjustments.

The suggested reorder quantity follows the inventory requirement:

```text
Reorder Quantity =
(Avg Daily Sales × Lead Time)
+ Safety Stock
- Current Stock
```

The actual implementation applies its configured decision rules and ensures that healthy and overstock products do not receive positive replenishment quantities.

Products with zero recorded daily sales are assigned a manual-review status rather than receiving an automatic replenishment suggestion.

## AI Explanation and Validation

BuildStock AI uses a local Qwen2.5 3B model through Ollama to generate product-specific explanations.

The rule-based engine remains responsible for inventory classifications and reorder quantities. AI-generated explanations do not independently determine purchasing decisions.

If an AI explanation is rejected or unavailable, the system uses a product-specific rule-based fallback.

## Testing Results

The project was tested using a dataset containing 22 construction products across 9 categories.

| Test Metric | Result |
|---|---:|
| Products analyzed | 22 |
| System tests passed | 44 |
| System tests failed | 0 |
| AI explanations accepted | 21 |
| Rule-based fallbacks | 1 |
| Structural validation passed | 22 |

**Overall Result: All 44 configured system tests passed.**

These tests verify data quality and consistency between system modules. They do not guarantee that every AI-generated statement is factually correct.

## Project Limitations

- Uses a predefined/mock construction inventory dataset.
- Does not connect to real-time Point of Sale (POS) systems.
- Does not integrate with ERP or Warehouse Management Systems.
- Does not automatically place purchase orders.
- Does not use machine-learning-based demand forecasting.
- All replenishment recommendations require human review and approval.

## Future Enhancements

- Real-time inventory integration.
- Barcode and QR-based stock updates.
- Advanced demand forecasting.
- Supplier and purchase-order integration.
- Multi-warehouse inventory management.
- Enhanced AI-assisted inventory analytics.

## Author

**Maajida A**

Computer Science and Engineering

GitHub: https://github.com/maajidaasif

LinkedIn: https://www.linkedin.com/in/maajida-a-195809279/

---

*BuildStock AI – Smarter Inventory Decisions for Construction Materials.*
