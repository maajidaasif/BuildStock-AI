
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path

# =========================================================
# BUILDSTOCK AI - PROFESSIONAL INVENTORY DASHBOARD
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
# PROFESSIONAL DARK UI STYLING
# =========================================================

st.markdown(
    """
    <style>
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stHeader"] {
        background-color: #0b1220 !important;
        color: #e7eefb !important;
    }

    [data-testid="stMainBlockContainer"] {
        color: #e7eefb !important;
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"] {
        color: #aab9d0;
    }

    .block-container {
        max-width: 1600px;
        padding: 2rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #101b32 !important;
        width: 340px !important;
        min-width: 340px !important;
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

    /* Navigation */
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

    /* Sidebar multiselect */
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

    /* Main headings */
    h1, h2, h3, h4 {
        color: #f1f6ff !important;
        letter-spacing: -0.3px;
    }

    /* KPI cards */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #142238, #101b2e);
        border: 1px solid #263a56;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 5px 18px rgba(0, 0, 0, 0.18);
    }

    [data-testid="stMetricLabel"] {
        color: #9fb2ce !important;
    }

    [data-testid="stMetricValue"] {
        color: #f4f8ff !important;
        font-weight: 700;
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 8px;
        border: 1px solid #315071;
        background: #14243a;
        color: #eaf4ff;
        font-weight: 600;
        min-height: 40px;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #10b9d0;
        color: #ffffff;
        background: #1a3450;
    }

    /* Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #263a56;
        border-radius: 10px;
        overflow: hidden;
    }

    /* Main inputs */
    [data-testid="stMain"] input {
        background: #142238 !important;
        color: #eef5ff !important;
        -webkit-text-fill-color: #eef5ff !important;
        border-color: #344b69 !important;
    }

    [data-testid="stMain"] input::placeholder {
        color: #8fa3bf !important;
        -webkit-text-fill-color: #8fa3bf !important;
    }

    [data-testid="stMain"] label,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] {
        color: #dce7f7;
    }

    /* Brand logo */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 13px;
        padding: 18px 0 0;
margin-top: 12px;
    }

    .brand-mark {
        width: 54px;
        height: 54px;
        min-width: 54px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 15px;
        background: linear-gradient(135deg, #0879d8 0%, #10c6c8 100%);
        box-shadow: 0 7px 18px rgba(8, 121, 216, 0.22);
    }

    .brand-mark svg {
        width: 43px;
        height: 43px;
    }

    .brand-name {
        color: #f2f7ff;
        font-size: 1.75rem;
        line-height: 1.1;
        font-weight: 850;
        letter-spacing: -0.8px;
    }

    .brand-name span {
        color: #089bbd;
    }

    .brand-tagline {
        color: #0b9db5;
        font-size: 0.65rem;
        font-weight: 800;
        letter-spacing: 1.65px;
        margin-top: 5px;
    }

    .dashboard-search-label {
        color: #a9c0dc;
        font-size: 0.88rem;
        font-weight: 700;
        margin: 0 0 5px 2px;
    }

    .app-footer {
        color: #91a4bf;
        font-size: 0.85rem;
        text-align: center;
        padding: 18px 0 5px;
    }

    @media (max-width: 700px) {
        .block-container {
            padding: 1rem;
        }
    }
    /* Hide Streamlit Deploy button */
[data-testid="stAppDeployButton"],
[data-testid="stDeployButton"],
.stDeployButton {
    display: none !important;
    visibility: hidden !important;
}
/* Bright highlighted urgent alert cards */
div[data-testid="stAlert"] {
    background: #3b1727 !important;
    border: 1px solid #ff4d79 !important;
    border-left: 5px solid #ff315c !important;
    border-radius: 12px !important;
    box-shadow: 0 0 14px rgba(255, 49, 92, 0.18) !important;
}

div[data-testid="stAlert"] > div,
div[data-testid="stAlert"] [role="alert"],
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
    background: transparent !important;
    color: #ffffff !important;
}

div[data-testid="stAlert"] p {
    color: #ffffff !important;
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
    missing = [c for c in columns if c not in data.columns]

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
    return f"{value:,.2f}".rstrip("0").rstrip(".")


# =========================================================
# HEADER AND REFRESH
# =========================================================

header_left, header_right = st.columns([5, 1])

with header_left:
    st.markdown(
        """
        <div class="brand-header">
            <div class="brand-mark">
                <svg viewBox="0 0 64 64" role="img"
                     aria-label="BuildStock AI logo">
                    <path d="M12 51V25L25 14V51M25 51V32L39 21V51M39 51V29L52 19V51"
                          fill="none" stroke="#ffffff" stroke-width="3.2"
                          stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M8 52H56" stroke="#d8f7ff" stroke-width="3"
                          stroke-linecap="round"/>
                    <circle cx="25" cy="14" r="3.2" fill="#b9f4ff"/>
                    <circle cx="39" cy="21" r="3.2" fill="#b9f4ff"/>
                    <path d="M25 14L39 8L49 12" fill="none"
                          stroke="#b9f4ff" stroke-width="2.2"
                          stroke-linecap="round"/>
                    <circle cx="49" cy="12" r="3" fill="#ffffff"/>
                </svg>
            </div>
            <div>
                <div class="brand-name">BuildStock <span>AI</span></div>
                <div class="brand-tagline">
                    CONSTRUCTION INVENTORY INTELLIGENCE
                </div>
            </div>
        </div>
        <p style="color:#71809a;margin:7px 0 0 2px;">
            Intelligent construction inventory optimization
        </p>
        """,
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown(
        "<div style='height: 18px;'></div>",
        unsafe_allow_html=True
    )

    if st.button("↻ Refresh Data", width="stretch"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# =========================================================
# LOAD INVENTORY CSV
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
    column for column in REQUIRED_COLUMNS if column not in df.columns
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

if df["product_id"].isna().any() or df["product_id"].duplicated().any():
    st.error("Inventory data contains missing or duplicate product IDs.")
    st.stop()

for column in ["product_name", "category", "unit", "decision_category"]:
    df[column] = df[column].fillna("").astype(str).str.strip()

if (
    df[["product_name", "category", "unit", "decision_category"]] == ""
).any().any():
    st.error("Inventory data contains missing product information.")
    st.stop()

invalid_statuses = sorted(
    set(df["decision_category"]) - set(STATUSES)
)

if invalid_statuses:
    st.error(f"Unknown inventory statuses: {invalid_statuses}")
    st.stop()

df["ai_explanation"] = df["ai_explanation"].fillna(
    "No AI explanation is available for this product."
).astype(str)

# =========================================================
# SIDEBAR BRANDING AND NAVIGATION
# =========================================================

with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:11px;
                    padding:8px 0 18px;">
            <div style="width:48px;height:48px;min-width:48px;
                        border-radius:14px;display:flex;
                        align-items:center;justify-content:center;
                        background:linear-gradient(135deg,#0879d8,#10c6c8);
                        box-shadow:0 6px 16px rgba(8,121,216,.25);">
                <svg viewBox="0 0 64 64" width="39" height="39"
                     aria-label="BuildStock AI">
                    <path d="M12 51V25L25 14V51M25 51V32L39 21V51M39 51V29L52 19V51"
                          fill="none" stroke="#ffffff" stroke-width="3.2"
                          stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M8 52H56" stroke="#d8f7ff"
                          stroke-width="3" stroke-linecap="round"/>
                    <path d="M25 14L39 8L49 12" fill="none"
                          stroke="#b9f4ff" stroke-width="2.2"
                          stroke-linecap="round"/>
                    <circle cx="25" cy="14" r="3.2" fill="#b9f4ff"/>
                    <circle cx="39" cy="8" r="3" fill="#ffffff"/>
                    <circle cx="49" cy="12" r="3" fill="#ffffff"/>
                </svg>
            </div>
            <div>
                <div style="font-size:1.22rem;font-weight:850;
                            color:#ffffff;line-height:1.15;">
                    BuildStock <span style="color:#42d7e8;">AI</span>
                </div>
                <div style="font-size:0.61rem;color:#72dce8;
                            margin-top:5px;font-weight:800;
                            letter-spacing:1.35px;">
                    INVENTORY INTELLIGENCE
                </div>
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
# DASHBOARD PRODUCT SEARCH
# =========================================================

search_text = ""

if page == "📊 Dashboard":
    search_col, hint_col = st.columns([2.2, 3.8])

    with search_col:
        st.markdown(
            '<div class="dashboard-search-label">SEARCH PRODUCTS</div>',
            unsafe_allow_html=True,
        )

        search_text = st.text_input(
            "Search by product name or ID",
            placeholder="e.g. Cement or CP006",
            key="dashboard_product_search",
            label_visibility="collapsed",
        )

    with hint_col:
        st.markdown(
            "<div style='padding-top:28px;color:#8190a7;font-size:.84rem;'>"
            "Find a construction material by its name or product ID. "
            "Your category and status filters remain active."
            "</div>",
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

    id_match = filtered_df["product_id"].astype(str).str.contains(
        search,
        case=False,
        na=False,
        regex=False,
    )

    filtered_df = filtered_df[product_match | id_match].copy()

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

    # Original dashboard charts retained.
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
            ["URGENT REORDER", "REORDER SOON", "OVERSTOCK RISK"]
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

    c1.metric("Products Needing Replenishment", len(reorder_df))

    c2.metric(
        "Urgent Products",
        int(
            (reorder_df["decision_category"] == "URGENT REORDER").sum()
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
            c for c in required_alert_columns if c not in alerts_df.columns
        ]

        if missing_alert_columns:
            st.error(f"Missing alert columns: {missing_alert_columns}")

        elif alerts_df.empty:
            st.info("No inventory alerts are available.")

        else:
            validate_numeric_columns(
                alerts_df,
                ["recommended_reorder_quantity"],
                "Inventory alerts",
            )

            if (
                alerts_df["product_id"].isna().any()
                or alerts_df["product_id"].duplicated().any()
            ):
                st.error(
                    "Alerts contain missing or duplicate product IDs."
                )
                st.stop()

            alerts_df["product_id"] = alerts_df["product_id"].astype(str)

            alerts_df["priority"] = (
                alerts_df["priority"].fillna("").astype(str).str.strip()
            )

            invalid_priorities = sorted(
                set(alerts_df["priority"]) - set(PRIORITIES)
            )

            if invalid_priorities:
                st.error(f"Unknown alert priorities: {invalid_priorities}")
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
                    (visible_alerts["priority"] == "P1 - CRITICAL").sum()
                ),
            )

            p2.metric(
                "🟠 High",
                int(
                    (visible_alerts["priority"] == "P2 - HIGH").sum()
                ),
            )

            p3.metric(
                "🟡 Review",
                int(
                    (visible_alerts["priority"] == "P3 - REVIEW").sum()
                ),
            )

            p4.metric(
                "🟢 Normal",
                int(
                    (visible_alerts["priority"] == "P4 - NORMAL").sum()
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

    validation_df = None

    if VALIDATION_FILE.exists():
        try:
            validation_df = load_data(
                str(VALIDATION_FILE),
                VALIDATION_FILE.stat().st_mtime_ns,
            )

            if "product_id" not in validation_df.columns:
                validation_df = None

        except (
            OSError,
            ValueError,
            pd.errors.ParserError,
            pd.errors.EmptyDataError,
        ):
            validation_df = None

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
                    f"{format_quantity(row['current_stock'])} {row['unit']}",
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

                # Rule-engine facts
                fact_columns = [
                    ("adjusted_safety_stock", "Adjusted Safety Stock"),
                    ("lead_time_demand", "Lead-Time Demand"),
                    ("effective_reorder_level", "Effective Reorder Level"),
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
                        fact_cols, available_facts
                    ):
                        fact_col.metric(
                            label,
                            f"{format_quantity(float(row[column]))} "
                            f"{row['unit']}",
                        )

                    st.caption(
                        "Values above come from the inventory pipeline output; "
                        "they are displayed separately from the LLM explanation."
                    )

                if (
                    "explanation_source" in row.index
                    and pd.notna(row["explanation_source"])
                ):
                    st.caption(
                        f"Explanation source: {row['explanation_source']}"
                    )

                if validation_df is not None:
                    match = validation_df[
                        validation_df["product_id"].astype(str)
                        == str(row["product_id"])
                    ]

                    if (
                        not match.empty
                        and "validation_status" in match.columns
                    ):
                        validation_status = str(
                            match.iloc[0]["validation_status"]
                        )

                        if validation_status == "PASS":
                            st.success(
                                "Structural validation: PASS — this does not "
                                "guarantee every sentence in the AI explanation "
                                "is factually correct."
                            )

                        else:
                            st.warning(
                                "Structural validation: REVIEW REQUIRED — "
                                + str(
                                    match.iloc[0].get(
                                        "validation_issues",
                                        "Check validation report.",
                                    )
                                )
                            )

                st.markdown("**AI-Generated Explanation**")
                st.write(row["ai_explanation"])


# =========================================================
# PAGE 6 - EXPORT REPORTS
# =========================================================

elif page == "📥 Export Reports":
    st.title("Export Reports")

    st.caption("Download inventory, reorder, and alert reports.")

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
            data=filtered_df.to_csv(
                index=False
            ).encode("utf-8"),
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
                    export_alerts = export_alerts[
                        export_alerts["product_id"].astype(str).isin(
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
