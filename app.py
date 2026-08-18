"""
Retail Analytics — Streamlit app
Run with:  streamlit run app.py
Reads the 5 CSVs from ./data/ and renders an interactive, filterable
multi-tab dashboard with an auto-generated plain-language summary per tab.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Retail Analytics", page_icon="📊", layout="wide")

# ---------------------------------------------------------------------------
# Palette (validated categorical / sequential set)
# ---------------------------------------------------------------------------
SURFACE       = "#fcfcfb"
INK_PRIMARY   = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED     = "#898781"
GRID          = "#e1e0d9"

CAT = {
    "blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "yellow": "#eda100",
    "magenta": "#e87ba4", "green": "#008300", "violet": "#4a3aa7", "red": "#e34948",
}
CAT_ORDER = ["blue", "orange", "aqua", "yellow", "magenta", "green", "violet", "red"]
CAT_SEQUENCE = [CAT[k] for k in CAT_ORDER]
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
STATUS_CRITICAL = "#d03b3b"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(color=INK_SECONDARY, family="system-ui, -apple-system, Segoe UI, sans-serif"),
    title_font=dict(color=INK_PRIMARY, size=16),
    margin=dict(t=50, l=10, r=10, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)

def style_fig(fig, y_title=None, x_title=None):
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(showgrid=False, linecolor=GRID, title=x_title)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, title=y_title)
    return fig

def money(x):
    if x >= 1_000_000:
        return f"${x/1_000_000:.1f}M"
    if x >= 1_000:
        return f"${x/1_000:.0f}K"
    return f"${x:.0f}"

# ---------------------------------------------------------------------------
# Data loading & cleaning
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    categories = pd.read_csv("data/categories.csv")
    products = pd.read_csv("data/products.csv")
    customers = pd.read_csv("data/customers.csv")
    orders = pd.read_csv("data/orders.csv")
    details = pd.read_csv("data/order_details.csv")

    orders["OrderDate"] = pd.to_datetime(orders["OrderDate"])
    customers["SignUpDate"] = pd.to_datetime(customers["SignUpDate"])

    details["IsReturned"] = details["IsReturned"].astype(int)
    details["ReturnDate"] = pd.to_datetime(details["ReturnDate"], errors="coerce")
    details.loc[details["ReturnDate"].dt.year == 9999, "ReturnDate"] = pd.NaT

    details["Revenue"] = details["Quantity"] * details["UnitPrice"] * (1 - details["DiscountRate"])
    details["Cost"] = details["Quantity"] * details["UnitCost"]
    details["Profit"] = details["Revenue"] - details["Cost"]

    df = (details
          .merge(orders, on="OrderID", how="left")
          .merge(products, on="ProductID", how="left")
          .merge(categories, on="CategoryID", how="left")
          .merge(customers, on="CustomerID", how="left"))

    df["OrderMonth"] = df["OrderDate"].dt.to_period("M").dt.to_timestamp()
    df["DayOfWeek"] = df["OrderDate"].dt.day_name()
    df["OrderHour"] = pd.to_datetime(df["OrderTime"], format="%H:%M:%S", errors="coerce").dt.hour

    return categories, products, customers, orders, details, df

categories, products, customers, orders, details, df_full = load_data()

# ---------------------------------------------------------------------------
# Sidebar filters (apply to every tab)
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

min_date, max_date = df_full["OrderDate"].min().date(), df_full["OrderDate"].max().date()
date_range = st.sidebar.date_input("Order date range", value=(min_date, max_date),
                                    min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

cat_options = sorted(df_full["CategoryName"].dropna().unique())
selected_cats = st.sidebar.multiselect("Category", cat_options, default=cat_options)

region_options = sorted(df_full["Region"].dropna().unique())
selected_regions = st.sidebar.multiselect("Region", region_options, default=region_options)

segment_options = sorted(df_full["CustomerSegment"].dropna().unique())
selected_segments = st.sidebar.multiselect("Customer segment", segment_options, default=segment_options)

df = df_full[
    (df_full["OrderDate"].dt.date >= start_date) &
    (df_full["OrderDate"].dt.date <= end_date) &
    (df_full["CategoryName"].isin(selected_cats)) &
    (df_full["Region"].isin(selected_regions)) &
    (df_full["CustomerSegment"].isin(selected_segments))
]

st.sidebar.caption(f"{len(df):,} of {len(df_full):,} line items match the current filters.")

if df.empty:
    st.warning("No data matches the current filters. Adjust the filters in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# Shared aggregates
# ---------------------------------------------------------------------------
total_revenue = df["Revenue"].sum()
total_profit = df["Profit"].sum()
total_orders = df["OrderID"].nunique()
total_customers = df["CustomerID"].nunique()
aov = total_revenue / total_orders if total_orders else 0
return_rate = df["IsReturned"].mean()
margin = total_profit / total_revenue if total_revenue else 0

st.title("📊 Retail Analytics Dashboard")
st.caption(f"{start_date} → {end_date}  ·  {total_orders:,} orders  ·  {total_customers:,} customers")

tab_overview, tab_products, tab_customers, tab_returns, tab_timing, tab_data = st.tabs(
    ["🏠 Overview", "🏷️ Categories & Products", "👥 Customers", "🔄 Returns", "🕐 Order Timing", "📄 Data Explorer"]
)

# ---------------------------------------------------------------------------
# TAB 1 — Overview
# ---------------------------------------------------------------------------
with tab_overview:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Revenue", money(total_revenue))
    c2.metric("Total Profit", money(total_profit))
    c3.metric("Margin", f"{margin*100:.1f}%")
    c4.metric("Orders", f"{total_orders:,}")
    c5.metric("Avg Order Value", money(aov))
    c6.metric("Return Rate", f"{return_rate*100:.1f}%")

    monthly = df.groupby("OrderMonth").agg(Revenue=("Revenue", "sum"),
                                            Orders=("OrderID", "nunique")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly["OrderMonth"], y=monthly["Revenue"], mode="lines",
                              line=dict(color=CAT["blue"], width=2.5), fill="tozeroy",
                              fillcolor="rgba(42,120,214,0.08)", name="Revenue",
                              hovertemplate="%{x|%b %Y}<br>Revenue: $%{y:,.0f}<extra></extra>"))
    style_fig(fig, y_title="Revenue ($)")
    fig.update_layout(title="Monthly Revenue Trend", height=380)
    st.plotly_chart(fig, use_container_width=True)

    top_cat = df.groupby("CategoryName")["Revenue"].sum().idxmax()
    top_cat_rev = df.groupby("CategoryName")["Revenue"].sum().max()
    top_region = df.groupby("Region")["Revenue"].sum().idxmax()
    top_region_rev = df.groupby("Region")["Revenue"].sum().max()
    best_month = monthly.loc[monthly["Revenue"].idxmax(), "OrderMonth"]
    best_month_rev = monthly["Revenue"].max()
    trend = "up" if monthly["Revenue"].iloc[-1] >= monthly["Revenue"].iloc[0] else "down"

    st.subheader("Summary")
    st.markdown(f"""
    - Across the selected filters, **{total_orders:,} orders** from **{total_customers:,} customers**
      generated **{money(total_revenue)}** in revenue and **{money(total_profit)}** in profit
      (**{margin*100:.1f}%** margin), for an average order value of **{money(aov)}**.
    - **{top_cat}** is the top-performing category (**{money(top_cat_rev)}**), and **{top_region}**
      is the top-performing region (**{money(top_region_rev)}**).
    - The strongest month on record is **{best_month:%B %Y}** at **{money(best_month_rev)}** in revenue,
      and the overall monthly trend across the filtered window is trending **{trend}**.
    - **{return_rate*100:.1f}%** of line items are returned — see the *Returns* tab for where that's concentrated.
    """)

# ---------------------------------------------------------------------------
# TAB 2 — Categories & Products
# ---------------------------------------------------------------------------
with tab_products:
    left, right = st.columns(2)

    cat_rev = df.groupby("CategoryName")["Revenue"].sum().sort_values(ascending=True)
    fig = px.bar(cat_rev, x=cat_rev.values, y=cat_rev.index, orientation="h",
                 color_discrete_sequence=[SEQ_BLUE[3]],
                 labels={"x": "Revenue ($)", "y": ""},
                 hover_data={"x": ":$,.0f"})
    fig.update_traces(hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>")
    style_fig(fig, x_title="Revenue ($)")
    fig.update_layout(title="Revenue by Category", height=420, showlegend=False)
    left.plotly_chart(fig, use_container_width=True)

    prod_rev = df.groupby("ProductName")["Revenue"].sum().sort_values(ascending=False).head(15).sort_values()
    fig2 = px.bar(prod_rev, x=prod_rev.values, y=prod_rev.index, orientation="h",
                  color_discrete_sequence=[SEQ_BLUE[3]])
    fig2.update_traces(hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>")
    style_fig(fig2, x_title="Revenue ($)")
    fig2.update_layout(title="Top 15 Products by Revenue", height=420, showlegend=False)
    right.plotly_chart(fig2, use_container_width=True)

    cat_qty = df.groupby("CategoryName").agg(Revenue=("Revenue", "sum"),
                                              Quantity=("Quantity", "sum"),
                                              Orders=("OrderID", "nunique")).reset_index()
    cat_qty["AvgOrderValue"] = cat_qty["Revenue"] / cat_qty["Orders"]
    fig3 = px.scatter(cat_qty, x="Quantity", y="Revenue", size="Orders", color="CategoryName",
                       color_discrete_sequence=CAT_SEQUENCE, hover_name="CategoryName",
                       labels={"Quantity": "Units sold", "Revenue": "Revenue ($)"})
    fig3.update_traces(marker=dict(line=dict(width=1, color=SURFACE)))
    style_fig(fig3, y_title="Revenue ($)", x_title="Units sold")
    fig3.update_layout(title="Category Volume vs. Revenue (bubble size = orders)", height=420)
    st.plotly_chart(fig3, use_container_width=True)

    top_prod_name = prod_rev.idxmax()
    top_prod_rev = prod_rev.max()
    n_cats = cat_rev.shape[0]
    top3_share = cat_rev.sort_values(ascending=False).head(3).sum() / cat_rev.sum()

    st.subheader("Summary")
    st.markdown(f"""
    - **{cat_rev.idxmax()}** is the leading category by revenue (**{money(cat_rev.max())}**), and the
      top 3 categories together account for **{top3_share*100:.0f}%** of filtered revenue across **{n_cats}** categories.
    - The single best-selling product is **{top_prod_name}** at **{money(top_prod_rev)}**.
    - The bubble chart shows which categories combine high volume *and* high revenue (top-right) versus
      categories that sell a lot of units at low value (bottom-right) or few high-value units (top-left).
    """)

# ---------------------------------------------------------------------------
# TAB 3 — Customers
# ---------------------------------------------------------------------------
with tab_customers:
    left, right = st.columns(2)

    seg_rev = df.groupby("CustomerSegment")["Revenue"].sum().sort_values(ascending=False)
    fig = px.bar(seg_rev, x=seg_rev.index, y=seg_rev.values,
                 color=seg_rev.index, color_discrete_sequence=CAT_SEQUENCE)
    fig.update_traces(hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>")
    style_fig(fig, y_title="Revenue ($)")
    fig.update_layout(title="Revenue by Customer Segment", height=380, showlegend=False)
    left.plotly_chart(fig, use_container_width=True)

    reg_rev = df.groupby("Region")["Revenue"].sum().sort_values(ascending=True)
    fig2 = px.bar(reg_rev, x=reg_rev.values, y=reg_rev.index, orientation="h",
                  color_discrete_sequence=[SEQ_BLUE[3]])
    fig2.update_traces(hovertemplate="%{y}<br>Revenue: $%{x:,.0f}<extra></extra>")
    style_fig(fig2, x_title="Revenue ($)")
    fig2.update_layout(title="Revenue by Region", height=380, showlegend=False)
    right.plotly_chart(fig2, use_container_width=True)

    left2, right2 = st.columns(2)
    cust_in_filter = customers[customers["CustomerID"].isin(df["CustomerID"])]
    fig3 = px.histogram(cust_in_filter, x="Age", nbins=20, color_discrete_sequence=[SEQ_BLUE[3]])
    fig3.add_vline(x=cust_in_filter["Age"].mean(), line_dash="dash", line_color=CAT["orange"])
    style_fig(fig3, y_title="Customers", x_title="Age")
    fig3.update_layout(title="Customer Age Distribution", height=360, showlegend=False)
    left2.plotly_chart(fig3, use_container_width=True)

    gender_rev = df.groupby("Gender")["Revenue"].sum().sort_values(ascending=False)
    fig4 = px.bar(gender_rev, x=gender_rev.index, y=gender_rev.values,
                  color=gender_rev.index, color_discrete_sequence=CAT_SEQUENCE)
    fig4.update_traces(hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>")
    style_fig(fig4, y_title="Revenue ($)")
    fig4.update_layout(title="Revenue by Gender", height=360, showlegend=False)
    right2.plotly_chart(fig4, use_container_width=True)

    top_segment = seg_rev.idxmax()
    top_seg_share = seg_rev.max() / seg_rev.sum()
    avg_age = cust_in_filter["Age"].mean()
    top_gender = gender_rev.idxmax()

    st.subheader("Summary")
    st.markdown(f"""
    - The **{top_segment}** segment drives the most revenue, **{top_seg_share*100:.0f}%** of the filtered total.
    - **{reg_rev.idxmax()}** is the top region (**{money(reg_rev.max())}**); the lowest is
      **{reg_rev.idxmin()}** (**{money(reg_rev.min())}**) — a gap worth investigating for expansion or marketing spend.
    - The average customer in this view is **{avg_age:.0f} years old**, and **{top_gender}** customers
      contribute the most revenue overall.
    """)

# ---------------------------------------------------------------------------
# TAB 4 — Returns
# ---------------------------------------------------------------------------
with tab_returns:
    left, right = st.columns(2)

    ret_by_cat = df.groupby("CategoryName")["IsReturned"].mean().sort_values(ascending=True) * 100
    overall = return_rate * 100
    colors = [STATUS_CRITICAL if v > overall else SEQ_BLUE[3] for v in ret_by_cat.values]
    fig = go.Figure(go.Bar(x=ret_by_cat.values, y=ret_by_cat.index, orientation="h",
                            marker_color=colors,
                            hovertemplate="%{y}<br>Return rate: %{x:.1f}%<extra></extra>"))
    fig.add_vline(x=overall, line_dash="dash", line_color=INK_MUTED,
                  annotation_text=f"avg {overall:.1f}%", annotation_font_color=INK_MUTED)
    style_fig(fig, x_title="% of line items returned")
    fig.update_layout(title="Return Rate by Category (red = above average)", height=420, showlegend=False)
    left.plotly_chart(fig, use_container_width=True)

    reasons = (df.loc[df["IsReturned"] == 1, "ReturnReason"]
                 .dropna().loc[lambda s: s.str.lower() != "none"]
                 .value_counts().head(8).sort_values())
    if len(reasons):
        fig2 = px.bar(reasons, x=reasons.values, y=reasons.index, orientation="h",
                      color_discrete_sequence=[CAT["orange"]])
        fig2.update_traces(hovertemplate="%{y}<br>Count: %{x:,}<extra></extra>")
        style_fig(fig2, x_title="Returned line items")
        fig2.update_layout(title="Top Return Reasons", height=420, showlegend=False)
        right.plotly_chart(fig2, use_container_width=True)
    else:
        right.info("No return reasons in the current filter selection.")

    worst_cat = ret_by_cat.idxmax()
    worst_rate = ret_by_cat.max()
    top_reason = reasons.idxmax() if len(reasons) else "N/A"
    lost_revenue = df.loc[df["IsReturned"] == 1, "Revenue"].sum()

    st.subheader("Summary")
    st.markdown(f"""
    - The overall return rate is **{overall:.1f}%**. **{worst_cat}** is the most return-prone category
      at **{worst_rate:.1f}%**, well above the average.
    - The leading return reason is **"{top_reason}"** — worth a closer look at product listings,
      packaging, or fulfillment accuracy for the categories above the average line.
    - Returned line items represent **{money(lost_revenue)}** in gross revenue exposure over this period.
    """)

# ---------------------------------------------------------------------------
# TAB 5 — Order Timing
# ---------------------------------------------------------------------------
with tab_timing:
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heat = (df.drop_duplicates("OrderID")
              .groupby(["DayOfWeek", "OrderHour"]).size()
              .unstack(fill_value=0).reindex(dow_order).reindex(columns=range(24), fill_value=0))

    fig = px.imshow(heat.values, x=[f"{h:02d}" for h in range(24)], y=dow_order,
                     color_continuous_scale=SEQ_BLUE, aspect="auto",
                     labels=dict(color="Orders"))
    fig.update_traces(hovertemplate="Day: %{y}<br>Hour: %{x}<br>Orders: %{z}<extra></extra>")
    style_fig(fig)
    fig.update_layout(title="Order Volume by Day of Week & Hour", height=420)
    st.plotly_chart(fig, use_container_width=True)

    hourly = df.drop_duplicates("OrderID").groupby("OrderHour").size()
    peak_hour = hourly.idxmax()
    daily = df.drop_duplicates("OrderID").groupby("DayOfWeek").size().reindex(dow_order)
    peak_day = daily.idxmax()
    quiet_hours = hourly[hourly < hourly.mean() * 0.3].index.tolist()

    st.subheader("Summary")
    st.markdown(f"""
    - **{peak_day}** is the busiest day of the week, and **{peak_hour}:00** is the busiest hour overall.
    - Order volume is heavily concentrated in two windows — around midday and again in the evening —
      with very little activity overnight{f" (roughly {min(quiet_hours):02d}:00–{max(quiet_hours):02d}:00)" if quiet_hours else ""}.
    - This pattern is useful for staffing customer support, scheduling promotions, or timing marketing sends.
    """)

# ---------------------------------------------------------------------------
# TAB 6 — Data Explorer
# ---------------------------------------------------------------------------
with tab_data:
    st.subheader("Filtered, merged dataset")
    st.dataframe(df.head(2000), use_container_width=True, height=450)
    st.caption(f"Showing up to 2,000 of {len(df):,} filtered rows.")

    st.download_button("Download filtered data as CSV",
                        data=df.to_csv(index=False).encode("utf-8"),
                        file_name="filtered_retail_data.csv", mime="text/csv")

    st.subheader("Source tables")
    src_tab1, src_tab2, src_tab3, src_tab4, src_tab5 = st.tabs(
        ["categories", "products", "customers", "orders", "order_details"])
    with src_tab1:
        st.dataframe(categories, use_container_width=True)
    with src_tab2:
        st.dataframe(products, use_container_width=True)
    with src_tab3:
        st.dataframe(customers, use_container_width=True)
    with src_tab4:
        st.dataframe(orders, use_container_width=True)
    with src_tab5:
        st.dataframe(details, use_container_width=True)
