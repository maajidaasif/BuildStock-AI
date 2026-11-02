import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path

# =========================================================
# BUILDSTOCK AI - PROFESSIONAL INVENTORY DASHBOARD
# MODULE 11: DASHBOARD INTEGRATION AND VERIFICATION
# =========================================================

ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = ROOT / "data" / "ai_inventory_explanations.csv"
ALERTS_FILE = ROOT / "data" / "inventory_alerts.csv"
VALIDATION_FILE = ROOT / "data" / "ai_explanation_validation.csv"

STATUSES = [
    "URGENT REORDER",
    "REORDER SOON",
    "OVERSTOCK RISK",
    "STOCK HEALTHY",
]

PRIORITIES = [
    "P1 - CRITICAL",
    "P2 - HIGH",
    "P3 - REVIEW",
    "P4 - NORMAL",
]

st.set_page_config(
    page_title="BuildStock AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# PROFESSIONAL UI STYLING
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f7fc;
        color: #172033;
    }

    [data-testid="stHeader"] {
        background-color: #f4f7fc;
    }

    .block-container {
        max-width: 1600px;
        padding: 2rem;
    }

    section[data-testid="stSidebar"] {
        background-color: #101b32 !important;
        width: 340px !important;
        min-width: 340px !important;
        flex-shrink: 0 !important;
        border-right: 1px solid #263753;
    }

    section[data-testid="stSidebar"] > div {
        width: 340px !important;
    }

    section[data-testid="stSidebar"] > div:first-child {
        padding: 1.5rem 1.15rem;
    }

    section[data-testid="stSidebar"] * {
        color: #edf3ff;
    }

    section[data-testid="stSidebar"]
    [data-testid="stMarkdownContainer"] p {
        color: #bdc9df;
    }

    section[data-testid="stSidebar"] hr {
        border-color: #34435e;
        margin: 1.2rem 0;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 8px;
        width: 100%;
    }

    section[data-testid="stSidebar"]
    div[role="radiogroup"] label {
        width: 100%;
        box-sizing: border-box;
        padding: 12px 14px;
        margin-bottom: 4px;
        border-radius: 9px;
        border: 1px solid transparent;
        background-color: transparent;
    }

    section[data-testid="stSidebar"]
    div[role="radiogroup"] label:hover {
        background-color: #22314c;
        border-color: #344767;
    }

    section[data-testid="stSidebar"]
    div[role="radiogroup"] label p {
        font-size: 0.95rem;
        line-height: 1.4;
        font-weight: 500;
    }

    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] input[type="text"] {
        background-color: #ffffff !important;
        color: #172033 !important;
        -webkit-text-fill-color: #172033 !important;
        caret-color: #172033 !important;
        border: 1px solid #cbd5e1 !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] input::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
        outline: none !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #ffffff;
        border-color: #cbd5e1;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] input {
        background-color: transparent !important;
        color: #172033 !important;
        -webkit-text-fill-color: #172033 !important;
    }

    section[data-testid="stSidebar"] label {
        font-size: 0.9rem;
    }

    h1, h2, h3 {
        color: #152541;
        letter-spacing: -0.3px;
    }

    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e9f3;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 3px 10px rgba(20, 35, 65, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: #60708b;
    }

    [data-testid="stMetricValue"] {
        color: #14233f;
        font-weight: 700;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 8px;
        border: 1px solid #d7e0ed;
        font-weight: 600;
        min-height: 40px;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #e1e7f0;
        border-radius: 10px;
        overflow: hidden;
    }

    .app-footer {
        color: #7b879a;
        font-size: 0.85rem;
        text-align: center;
        padding: 18px 0 5px;
    }

    @media (max-width: 700px) {
        .block-container {
            padding: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# DATA LOADING AND VALIDATION
# =========================================================

@st.cache_data
def load_data(file_path, modified_time_ns):
    """Reload cached CSV data when the file changes."""
    return pd.read_csv(file_path)


def show_csv_error(error, label):
    st.error(f"Unable to load {label}: {error}")


def validate_numeric_columns(data, columns, label):
    """Validate required numeric fields."""
    missing = [column for column in columns if column not in data.columns]

    if missing:
        st.error(f"{label}: missing numeric columns: {missing}")
        st.stop()

    for column in columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    values = data[columns].to_numpy(dtype=float)

    if not np.isfinite(values).all():
        st.error(
            f"{label} contains missing, invalid, or infinite numbers."
        )
        st.stop()

    if (data[columns] < 0).any().any():
        st.error(f"{label} contains negative numeric values.")
        st.stop()


def format_quantity(value):
    """Format inventory quantities for display."""
    return f"{float(value):,.2f}".rstrip("0").rstrip(".")


def load_optional_validation():
    """Load the Module 10 validation report if available."""
    if not VALIDATION_FILE.exists():
        return None

    try:
        validation_df = load_data(
            str(VALIDATION_FILE),
            VALIDATION_FILE.stat().st_mtime_ns,
        )

        required = {"product_id", "validation_status"}

        if not required.issubset(validation_df.columns):
            return None

        validation_df["product_id"] = (
            validation_df["product_id"].astype(str).str.strip()
        )

        if validation_df["product_id"].duplicated().any():
            return None

        return validation_df

    except (
        OSError,
        ValueError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
    ):
        return None


# =========================================================
# HEADER AND REFRESH
# =========================================================

header_left, header_right = st.columns([5, 1])

with header_left:
    st.markdown(
        """
        <h1 style="margin-bottom:0;color:#142541;">
            🏗️ BuildStock AI
        </h1>
        <p style="color:#71809a;margin-top:5px;">
            Intelligent Construction Inventory Management
        </p>
        """,
        unsafe_allow_html=True,
    )

with header_right:
    if st.button("🔄 Refresh Data", width="stretch"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# =========================================================
# LOAD INVENTORY DATA
# =========================================================

if not DATA_FILE.exists():
    st.error(f"Inventory data file not found: {DATA_FILE}")
    st.info("Run the inventory pipeline first:")
    st.code("python -u src/run_pipeline.py")
    st.stop()

try:
    df = load_data(
        str(DATA_FILE),
        DATA_FILE.stat().st_mtime_ns,
    )
except (
    OSError,
    ValueError,
    pd.errors.ParserError,
    pd.errors.EmptyDataError,
) as error:
    show_csv_error(error, "inventory data")
    st.stop()

REQUIRED_COLUMNS = [
    "product_id",
    "product_name",
    "category",
    "unit",
    "current_stock",
    "avg_daily_sales",
    "decision_category",
    "recommended_reorder_quantity",
    "ai_explanation",
]

missing_columns = [
    column for column in REQUIRED_COLUMNS
    if column not in df.columns
]

if missing_columns:
    st.error(f"Missing inventory columns: {missing_columns}")
    st.stop()

if df.empty:
    st.warning("No inventory products are available.")
    st.stop()

validate_numeric_columns(
    df,
    [
        "current_stock",
        "avg_daily_sales",
        "recommended_reorder_quantity",
    ],
    "Inventory data",
)

df["product_id"] = df["product_id"].astype(str).str.strip()

if (
    df["product_id"].isna().any()
    or (df["product_id"] == "").any()
    or df["product_id"].duplicated().any()
):
    st.error("Inventory data contains missing or duplicate product IDs.")
    st.stop()

for column in [
    "product_name",
    "category",
    "unit",
    "decision_category",
]:
    df[column] = df[column].fillna("").astype(str).str.strip()

if (
    df[
        ["product_name", "category", "unit", "decision_category"]
    ] == ""
).any().any():
    st.error("Inventory data contains missing product information.")
    st.stop()

invalid_statuses = sorted(
    set(df["decision_category"]) - set(STATUSES)
)

if invalid_statuses:
    st.error(f"Unknown inventory statuses: {invalid_statuses}")
    st.stop()

df["ai_explanation"] = (
    df["ai_explanation"]
    .fillna("No AI explanation is available for this product.")
    .astype(str)
    .str.strip()
)

df.loc[
    df["ai_explanation"] == "",
    "ai_explanation",
] = "No AI explanation is available for this product."

# =========================================================
# SIDEBAR BRANDING AND NAVIGATION
# =========================================================

with st.sidebar:
    st.markdown(
        """
        <div style="padding:8px 0 18px;">
            <div style="font-size:2.5rem;">🏗️</div>
            <div style="font-size:1.5rem;font-weight:800;color:#ffffff;">
                BuildStock AI
            </div>
            <div style="font-size:0.8rem;color:#91a5c6;margin-top:5px;">
                INVENTORY INTELLIGENCE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### NAVIGATION")

    page = st.radio(
        "Choose a section",
        [
            "📊 Dashboard",
            "📋 Inventory",
            "🛒 Reorder Recommendations",
            "🚨 Alerts & Risks",
            "🤖 AI Explanations",
            "📥 Export Reports",
        ],
        index=0,
        label_visibility="collapsed",
        key="main_navigation",
    )

    st.divider()
    st.markdown("### INVENTORY FILTERS")

    categories = sorted(df["category"].unique().tolist())

    selected_categories = st.multiselect(
        "Product category",
        options=categories,
        default=categories,
        key="category_filter",
    )

    available_statuses = [
        status for status in STATUSES
        if status in df["decision_category"].unique()
    ]

    selected_statuses = st.multiselect(
        "Inventory status",
        options=STATUSES,
        default=available_statuses,
        key="status_filter",
    )

    search_text = st.text_input(
        "Search product",
        placeholder="Name or product ID...",
        key="product_search",
    )

    st.divider()

    st.markdown(
        f"""
        <div style="font-size:0.9rem;color:#bdc9df;">
            <b>DATA SOURCE</b><br>
            Inventory CSV<br><br>
            <b>PRODUCTS LOADED</b><br>
            {len(df)}
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# SHARED FILTERS
# =========================================================

filtered_df = df[
    df["category"].isin(selected_categories)
    & df["decision_category"].isin(selected_statuses)
].copy()

if search_text.strip():
    search = search_text.strip()

    product_match = filtered_df["product_name"].str.contains(
        search,
        case=False,
        na=False,
        regex=False,
    )

    id_match = filtered_df["product_id"].str.contains(
        search,
        case=False,
        na=False,
        regex=False,
    )

    filtered_df = filtered_df[
        product_match | id_match
    ].copy()

total_products = len(filtered_df)

urgent_count = int(
    (filtered_df["decision_category"] == "URGENT REORDER").sum()
)

reorder_soon_count = int(
    (filtered_df["decision_category"] == "REORDER SOON").sum()
)

overstock_count = int(
    (filtered_df["decision_category"] == "OVERSTOCK RISK").sum()
)

healthy_count = int(
    (filtered_df["decision_category"] == "STOCK HEALTHY").sum()
)

# =========================================================
# PAGE 1 - DASHBOARD
# =========================================================

if page == "📊 Dashboard":
    st.title("Inventory Overview")
    st.caption(
        "Monitor construction materials and identify inventory risks."
    )

    m1, m2, m3, m4, m5 = st.columns(5)

    m1.metric("Total Products", total_products)
    m2.metric("Urgent Reorder", urgent_count)
    m3.metric("Reorder Soon", reorder_soon_count)
    m4.metric("Overstock Risk", overstock_count)
    m5.metric("Stock Healthy", healthy_count)

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("📦 Inventory Status Distribution")

        status_counts = (
            filtered_df["decision_category"]
            .value_counts()
            .reindex(STATUSES, fill_value=0)
        )

        st.bar_chart(status_counts, color="#2457d6")

    with right:
        st.subheader("🧱 Products by Category")

        category_counts = filtered_df["category"].value_counts()
        st.bar_chart(category_counts, color="#16a6a1")

    st.divider()
    st.subheader("⚠️ Products Requiring Attention")

    attention_df = filtered_df[
        filtered_df["decision_category"].isin(
            [
                "URGENT REORDER",
                "REORDER SOON",
                "OVERSTOCK RISK",
            ]
        )
    ]

    if attention_df.empty:
        st.success("No products require attention in this view.")
    else:
        st.dataframe(
            attention_df[
                [
                    "product_id",
                    "product_name",
                    "current_stock",
                    "unit",
                    "decision_category",
                    "recommended_reorder_quantity",
                ]
            ],
            width="stretch",
            hide_index=True,
        )

    st.caption(f"Showing {total_products} of {len(df)} products.")

# =========================================================
# PAGE 2 - INVENTORY
# =========================================================

elif page == "📋 Inventory":
    st.title("Product Inventory")
    st.caption("Review stock levels and product classifications.")

    st.metric("Products in Current View", total_products)

    if filtered_df.empty:
        st.info("No products match your filters.")
    else:
        st.dataframe(
            filtered_df[
                [
                    "product_id",
                    "product_name",
                    "category",
                    "current_stock",
                    "unit",
                    "avg_daily_sales",
                    "decision_category",
                    "recommended_reorder_quantity",
                ]
            ],
            width="stretch",
            hide_index=True,
        )

        st.subheader("Inventory Status Distribution")

        st.bar_chart(
            filtered_df["decision_category"]
            .value_counts()
            .reindex(STATUSES, fill_value=0),
            color="#2457d6",
        )

# =========================================================
# PAGE 3 - REORDER RECOMMENDATIONS
# =========================================================

elif page == "🛒 Reorder Recommendations":
    st.title("Reorder Recommendations")
    st.caption(
        "Review suggested replenishment quantities before purchasing."
    )

    reorder_df = filtered_df[
        filtered_df["recommended_reorder_quantity"] > 0
    ].copy()

    c1, c2 = st.columns(2)

    c1.metric(
        "Products Needing Replenishment",
        len(reorder_df),
    )

    c2.metric(
        "Urgent Products",
        int(
            (
                reorder_df["decision_category"]
                == "URGENT REORDER"
            ).sum()
        ),
    )

    if reorder_df.empty:
        st.success("No positive reorder recommendations in this view.")
    else:
        st.dataframe(
            reorder_df[
                [
                    "product_id",
                    "product_name",
                    "current_stock",
                    "unit",
                    "decision_category",
                    "recommended_reorder_quantity",
                ]
            ],
            width="stretch",
            hide_index=True,
        )

        st.download_button(
            "📥 Download Reorder Recommendations",
            data=reorder_df.to_csv(index=False).encode("utf-8"),
            file_name="buildstock_reorder_recommendations.csv",
            mime="text/csv",
        )

        st.info(
            "Recommendations are suggestions. Confirm supplier packaging, "
            "availability, and purchasing requirements before ordering."
        )

# =========================================================
# PAGE 4 - ALERTS AND RISKS
# =========================================================

elif page == "🚨 Alerts & Risks":
    st.title("Inventory Alerts & Risk Prioritization")
    st.caption("Alerts support human review and do not place orders.")

    if not ALERTS_FILE.exists():
        st.warning(
            "Inventory alerts file not found. Run the pipeline to generate it."
        )
    else:
        try:
            alerts_df = load_data(
                str(ALERTS_FILE),
                ALERTS_FILE.stat().st_mtime_ns,
            )
        except (
            OSError,
            ValueError,
            pd.errors.ParserError,
            pd.errors.EmptyDataError,
        ) as error:
            show_csv_error(error, "inventory alerts")
            st.stop()

        required_alert_columns = [
            "product_id",
            "product_name",
            "decision_category",
            "priority",
            "recommended_reorder_quantity",
            "unit",
            "alert_message",
        ]

        missing_alert_columns = [
            column for column in required_alert_columns
            if column not in alerts_df.columns
        ]

        if missing_alert_columns:
            st.error(
                f"Missing alert columns: {missing_alert_columns}"
            )
        elif alerts_df.empty:
            st.info("No inventory alerts are available.")
        else:
            validate_numeric_columns(
                alerts_df,
                ["recommended_reorder_quantity"],
                "Inventory alerts",
            )

            alerts_df["product_id"] = (
                alerts_df["product_id"].fillna("").astype(str).str.strip()
            )

            if (
                (alerts_df["product_id"] == "").any()
                or alerts_df["product_id"].duplicated().any()
            ):
                st.error(
                    "Alerts contain missing or duplicate product IDs."
                )
                st.stop()

            alerts_df["priority"] = (
                alerts_df["priority"].fillna("").astype(str).str.strip()
            )

            invalid_priorities = sorted(
                set(alerts_df["priority"]) - set(PRIORITIES)
            )

            if invalid_priorities:
                st.error(
                    f"Unknown alert priorities: {invalid_priorities}"
                )
                st.stop()

            filtered_ids = set(filtered_df["product_id"].astype(str))

            visible_alerts = alerts_df[
                alerts_df["product_id"].isin(filtered_ids)
            ].copy()

            selected_priorities = st.multiselect(
                "Alert priority",
                options=PRIORITIES,
                default=PRIORITIES,
                key="alert_priority_filter",
            )

            visible_alerts = visible_alerts[
                visible_alerts["priority"].isin(selected_priorities)
            ].copy()

            p1, p2, p3, p4 = st.columns(4)

            p1.metric(
                "🔴 Critical",
                int(
                    (
                        visible_alerts["priority"]
                        == "P1 - CRITICAL"
                    ).sum()
                ),
            )

            p2.metric(
                "🟠 High",
                int(
                    (
                        visible_alerts["priority"]
                        == "P2 - HIGH"
                    ).sum()
                ),
            )

            p3.metric(
                "🟡 Review",
                int(
                    (
                        visible_alerts["priority"]
                        == "P3 - REVIEW"
                    ).sum()
                ),
            )

            p4.metric(
                "🟢 Normal",
                int(
                    (
                        visible_alerts["priority"]
                        == "P4 - NORMAL"
                    ).sum()
                ),
            )

            critical_alerts = visible_alerts[
                visible_alerts["priority"] == "P1 - CRITICAL"
            ]

            if not critical_alerts.empty:
                st.subheader("🔴 Immediate Attention Required")

                for _, alert in critical_alerts.iterrows():
                    st.error(
                        f"**{alert['product_name']} "
                        f"({alert['product_id']})**\n\n"
                        f"{alert['alert_message']}"
                    )

            st.subheader("All Inventory Alerts")

            if visible_alerts.empty:
                st.info("No alerts match the selected filters.")
            else:
                st.dataframe(
                    visible_alerts[required_alert_columns],
                    width="stretch",
                    hide_index=True,
                )

                st.download_button(
                    "📥 Download Inventory Alerts CSV",
                    data=visible_alerts.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="buildstock_inventory_alerts.csv",
                    mime="text/csv",
                    key="download_inventory_alerts",
                )

            inventory_ids = set(df["product_id"].astype(str))
            alert_ids = set(alerts_df["product_id"].astype(str))

            if inventory_ids != alert_ids:
                st.warning(
                    "Inventory and alert product IDs differ. "
                    "Rerun the pipeline to synchronize the CSV files."
                )

# =========================================================
# PAGE 5 - AI EXPLANATIONS
# =========================================================

elif page == "🤖 AI Explanations":
    st.title("AI Inventory Explanations")

    st.caption(
        "Review rule-engine inventory facts separately from the local AI narrative."
    )

    st.info(
        "The validation report checks structural and cross-file consistency. "
        "It does not prove that every statement generated by the LLM is "
        "factually correct. Review explanations before making purchasing decisions."
    )

    validation_df = load_optional_validation()

    if validation_df is None:
        st.warning(
            "The Module 10 validation report is missing or could not be read. "
            "Run: python src/validate_ai_explanations.py"
        )

    if filtered_df.empty:
        st.info("No products match your filters.")
    else:
        st.caption(
            f"{len(filtered_df)} product explanations available."
        )

        for _, row in filtered_df.iterrows():
            with st.expander(
                f"{row['product_name']} ({row['product_id']}) — "
                f"{row['decision_category']}"
            ):
                a, b, c = st.columns(3)

                a.metric(
                    "Current Stock",
                    f"{format_quantity(row['current_stock'])} "
                    f"{row['unit']}",
                )

                b.metric(
                    "Daily Sales",
                    format_quantity(row["avg_daily_sales"]),
                )

                c.metric(
                    "Rule-Based Reorder Suggestion",
                    f"{format_quantity(row['recommended_reorder_quantity'])} "
                    f"{row['unit']}",
                )

                status = row["decision_category"]

                if status == "URGENT REORDER":
                    st.error(status)
                elif status == "REORDER SOON":
                    st.warning(status)
                elif status == "OVERSTOCK RISK":
                    st.info(status)
                else:
                    st.success(status)

                # Display verified pipeline facts separately from LLM text.
                fact_columns = [
                    (
                        "adjusted_safety_stock",
                        "Adjusted Safety Stock",
                    ),
                    (
                        "lead_time_demand",
                        "Lead-Time Demand",
                    ),
                    (
                        "effective_reorder_level",
                        "Effective Reorder Level",
                    ),
                ]

                available_facts = [
                    (column, label)
                    for column, label in fact_columns
                    if column in row.index and pd.notna(row[column])
                ]

                if available_facts:
                    st.markdown("**Rule-Engine Facts**")

                    fact_cols = st.columns(len(available_facts))

                    for fact_col, (column, label) in zip(
                        fact_cols,
                        available_facts,
                    ):
                        fact_col.metric(
                            label,
                            f"{format_quantity(float(row[column]))} "
                            f"{row['unit']}",
                        )

                    st.caption(
                        "These figures are read from the inventory pipeline "
                        "output and are shown separately from the LLM narrative."
                    )
                else:
                    st.caption(
                        "Detailed safety-stock and reorder-level fields are "
                        "not available in this CSV."
                    )

                if (
                    "explanation_source" in row.index
                    and pd.notna(row["explanation_source"])
                ):
                    st.caption(
                        f"Explanation source: {row['explanation_source']}"
                    )

                # Show the Module 10 structural validation result.
                if validation_df is not None:
                    matches = validation_df[
                        validation_df["product_id"].astype(str)
                        == str(row["product_id"])
                    ]

                    if not matches.empty:
                        validation_row = matches.iloc[0]
                        validation_status = str(
                            validation_row["validation_status"]
                        ).strip().upper()

                        if validation_status == "PASS":
                            st.success(
                                "Structural validation: PASS. "
                                "This does not guarantee that every sentence "
                                "in the AI explanation is factually correct."
                            )
                        else:
                            issues = validation_row.get(
                                "validation_issues",
                                "Check the validation report.",
                            )

                            st.warning(
                                "Structural validation: REVIEW REQUIRED. "
                                f"{issues}"
                            )
                    else:
                        st.warning(
                            "No validation result was found for this product."
                        )

                st.markdown("**AI-Generated Explanation**")
                st.write(row["ai_explanation"])

                st.caption(
                    "Purchasing decisions require human review. "
                    "The AI explanation does not place orders."
                )

# =========================================================
# PAGE 6 - EXPORT REPORTS
# =========================================================

elif page == "📥 Export Reports":
    st.title("Export Reports")
    st.caption(
        "Download inventory, reorder, and alert reports."
    )

    st.metric("Products Included", len(filtered_df))

    if filtered_df.empty:
        st.info("No products match the current filters.")
    else:
        st.subheader("Inventory Report")

        st.dataframe(
            filtered_df,
            width="stretch",
            hide_index=True,
        )

        st.download_button(
            "📥 Download Filtered Inventory CSV",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name="buildstock_inventory_report.csv",
            mime="text/csv",
            key="download_inventory_report",
            type="primary",
        )

        reorder_export = filtered_df[
            filtered_df["recommended_reorder_quantity"] > 0
        ].copy()

        st.subheader("Reorder Report")

        st.download_button(
            "📥 Download Reorder Report CSV",
            data=reorder_export.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="buildstock_reorder_report.csv",
            mime="text/csv",
            key="download_reorder_report",
        )

        if ALERTS_FILE.exists():
            try:
                export_alerts = load_data(
                    str(ALERTS_FILE),
                    ALERTS_FILE.stat().st_mtime_ns,
                )

                if "product_id" in export_alerts.columns:
                    export_alerts["product_id"] = (
                        export_alerts["product_id"].astype(str)
                    )

                    export_alerts = export_alerts[
                        export_alerts["product_id"].isin(
                            set(filtered_df["product_id"].astype(str))
                        )
                    ]

                    st.download_button(
                        "📥 Download Filtered Alerts CSV",
                        data=export_alerts.to_csv(
                            index=False
                        ).encode("utf-8"),
                        file_name="buildstock_filtered_alerts.csv",
                        mime="text/csv",
                        key="download_filtered_alerts",
                    )

            except (
                OSError,
                ValueError,
                pd.errors.ParserError,
                pd.errors.EmptyDataError,
            ) as error:
                st.warning(
                    f"Unable to prepare alerts export: {error}"
                )

        if VALIDATION_FILE.exists():
            try:
                export_validation = load_data(
                    str(VALIDATION_FILE),
                    VALIDATION_FILE.stat().st_mtime_ns,
                )

                st.subheader("AI Explanation Validation Report")

                st.download_button(
                    "📥 Download AI Validation Report CSV",
                    data=export_validation.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="buildstock_ai_validation_report.csv",
                    mime="text/csv",
                    key="download_validation_report",
                )

            except (
                OSError,
                ValueError,
                pd.errors.ParserError,
                pd.errors.EmptyDataError,
            ) as error:
                st.warning(
                    f"Unable to prepare validation report: {error}"
                )

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    <div class="app-footer">
        <b>BuildStock AI</b> · Construction Inventory Optimization<br>
        Rule-based decisions · Local AI explanations ·
        Human-reviewed recommendations
    </div>
    """,
    unsafe_allow_html=True,
)
