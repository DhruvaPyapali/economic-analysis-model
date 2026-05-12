"""
Streamlit UI for the Simple analysis path of the Economic Analysis workbook.

Run: streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Allow `streamlit run` from any cwd
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from economics_model import GrowthMethod, SimpleModelInputs, run_simple_model

st.set_page_config(page_title="Economic Analysis (Simple)", layout="wide")

st.title("Economic Analysis Model — Simple path")
st.caption(
    "Interactive port of the **Simple** sheets: scenario-weighted projections, "
    "combined revenue build-up, and valuation heuristics from the Excel model."
)

with st.sidebar:
    st.header("Scenario")
    growth_method: GrowthMethod = st.selectbox(
        "Growth / risk treatment (Dashboard C27)",
        [
            "Other",
            "Discrete (Weighted Cash Flows)",
        ],
        index=0,
        help='Excel uses the literal string "Discrete (Weighted Cash Flows)" to unlock scenario weights.',
    )
    risk_free = st.number_input("Risk-free rate (C28)", value=0.0278, format="%.4f")
    p_opt = st.slider("Optimistic probability (C29)", 0.0, 1.0, 0.0, 0.01)
    p_pess = st.slider("Pessimistic probability (C30)", 0.0, 1.0, 0.0, 0.01)
    if p_opt + p_pess > 1.0:
        st.error("Optimistic + pessimistic probabilities cannot exceed 100%.")
    margins_same = st.checkbox("Margins same in each scenario (C32 = Yes)", value=True)

    st.divider()
    st.header("Multiples (Combined sheet)")
    pe_ratio = st.number_input("P / gross earnings (B27)", value=20.0, min_value=0.0)
    peg_ratio = st.number_input("PEG ratio (B31)", value=2.0, min_value=0.0)
    ps_ratio = st.number_input("P / sales (B35)", value=4.0, min_value=0.0)

col_a, col_t = st.columns(2)

with col_a:
    st.subheader("Acquirer (Dashboard F26–F37)")
    ar = st.number_input("Revenue", key="ar", min_value=0.0, value=0.0, format="%.2f")
    ac = st.number_input("Cost of goods sold", key="ac", min_value=0.0, value=0.0, format="%.2f")
    ae = st.number_input("EBITDA", key="ae", min_value=0.0, value=0.0, format="%.2f")
    ag = st.number_input("Historical revenue growth (decimal)", key="ag", value=0.0, format="%.4f")
    st.markdown("**Scenario growth (sales, decimal)**")
    ago = st.number_input("Optimistic sales growth", key="ago", value=0.0, format="%.4f")
    agp = st.number_input("Pessimistic sales growth", key="agp", value=0.0, format="%.4f")
    if not margins_same:
        st.markdown("**Scenario margins (when C32 = No)**")
        agmo = st.number_input("Optimistic gross margin", key="agmo", value=0.0, format="%.4f")
        agmp = st.number_input("Pessimistic gross margin", key="agmp", value=0.0, format="%.4f")
        aemo = st.number_input("Optimistic EBITDA margin", key="aemo", value=0.0, format="%.4f")
        aemp = st.number_input("Pessimistic EBITDA margin", key="aemp", value=0.0, format="%.4f")
    else:
        agmo = agmp = aemo = aemp = 0.0

with col_t:
    st.subheader("Target (Dashboard I26–I37)")
    tr = st.number_input("Revenue", key="tr", min_value=0.0, value=0.0, format="%.2f")
    tc = st.number_input("Cost of goods sold", key="tc", min_value=0.0, value=0.0, format="%.2f")
    te = st.number_input("EBITDA", key="te", min_value=0.0, value=0.0, format="%.2f")
    tg = st.number_input("Historical revenue growth (decimal)", key="tg", value=0.0, format="%.4f")
    st.markdown("**Scenario growth (sales, decimal)**")
    tgo = st.number_input("Optimistic sales growth ", key="tgo", value=0.0, format="%.4f")
    tgp = st.number_input("Pessimistic sales growth ", key="tgp", value=0.0, format="%.4f")
    if not margins_same:
        st.markdown("**Scenario margins (when C32 = No)**")
        tgmo = st.number_input("Optimistic gross margin ", key="tgmo", value=0.0, format="%.4f")
        tgmp = st.number_input("Pessimistic gross margin ", key="tgmp", value=0.0, format="%.4f")
        temo = st.number_input("Optimistic EBITDA margin ", key="temo", value=0.0, format="%.4f")
        temp = st.number_input("Pessimistic EBITDA margin ", key="temp", value=0.0, format="%.4f")
    else:
        tgmo = tgmp = temo = temp = 0.0

inp = SimpleModelInputs(
    growth_method=growth_method,
    risk_free_rate=risk_free,
    optimistic_probability=p_opt,
    pessimistic_probability=p_pess,
    margins_same_each_scenario=margins_same,
    acquirer_revenue=ar,
    acquirer_cogs=ac,
    acquirer_ebitda=ae,
    acquirer_hist_revenue_growth=ag,
    acquirer_opt_sales_growth=ago,
    acquirer_pess_sales_growth=agp,
    acquirer_opt_gross_margin=agmo,
    acquirer_pess_gross_margin=agmp,
    acquirer_opt_ebitda_margin=aemo,
    acquirer_pess_ebitda_margin=aemp,
    target_revenue=tr,
    target_cogs=tc,
    target_ebitda=te,
    target_hist_revenue_growth=tg,
    target_opt_sales_growth=tgo,
    target_pess_sales_growth=tgp,
    target_opt_gross_margin=tgmo,
    target_pess_gross_margin=tgmp,
    target_opt_ebitda_margin=temo,
    target_pess_ebitda_margin=temp,
    pe_ratio=pe_ratio,
    peg_ratio=peg_ratio,
    ps_ratio=ps_ratio,
)

if p_opt + p_pess > 1.0:
    st.stop()

res = run_simple_model(inp)

mcol1, mcol2, mcol3, mcol4 = st.columns(4)
mcol1.metric("Discount rate used", f"{res.discount_rate:.2%}")
mcol2.metric("NPV (10y target gross profit)", f"{res.npv_gross_profit_10y:,.0f}")
mcol3.metric("Terminal-style NPV (Simple target)", f"{res.valuation_terminal_style:,.0f}")
_g2 = res.yoy_revenue_growth[2]
mcol4.metric(
    "YoY rev. growth (yr 1 → 2)",
    f"{_g2:.2%}" if res.combined_gross_sales[1] > 0 and pd.notna(_g2) else "—",
)

st.subheader("Heuristic target prices (per workbook)")
vcol1, vcol2, vcol3 = st.columns(3)
vcol1.metric("Method 2 — P / gross earnings × year-0 GP", f"{res.price_pe:,.0f}")
vcol2.metric("Method 3 — PEG-style", f"{res.price_peg:,.0f}")
vcol3.metric("Method 4 — P / sales × revenue", f"{res.price_ps:,.0f}")

years = list(range(11))
df = pd.DataFrame(
    {
        "Year": years,
        "Combined gross sales": res.combined_gross_sales,
        "Combined gross profit": res.combined_gross_profit,
        "Combined gross margin": res.combined_gross_margin,
        "YoY revenue growth": res.yoy_revenue_growth,
        "Target gross profit": res.target.gross_profit,
        "Acquirer gross profit": res.acquirer.gross_profit,
    }
)

tab1, tab2 = st.tabs(["Charts", "Tables"])
with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=res.combined_gross_sales, name="Combined gross sales", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=years, y=res.combined_gross_profit, name="Combined gross profit", mode="lines+markers"))
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="Currency (same units as inputs)",
        xaxis_title="Year",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    disp = df.copy()
    for c in ["Combined gross sales", "Combined gross profit", "Target gross profit", "Acquirer gross profit"]:
        disp[c] = disp[c].map(lambda x: f"{x:,.2f}")
    disp["Combined gross margin"] = disp["Combined gross margin"].map(lambda x: f"{x:.2%}")
    disp["YoY revenue growth"] = disp["YoY revenue growth"].map(lambda x: "—" if pd.isna(x) else f"{x:.2%}")
    st.dataframe(disp, use_container_width=True, hide_index=True)

with st.expander("Scenario weights (derived)"):
    st.write(
        {
            "Optimistic": res.target.p_opt,
            "Status quo": res.target.p_sq,
            "Pessimistic": res.target.p_pess,
            "Weighted sales growth (target)": res.target.w_sales_growth,
            "Weighted gross margin (target)": res.target.w_gross_margin,
            "Weighted EBITDA margin (target)": res.target.w_ebitda_margin,
        }
    )

st.caption(
    "Note: Excel cell **Combined Company Value-Simple!B25** references **Variables of Target-Complex**; "
    "this app applies the same terminal cash-flow pattern using the **Simple** target projection instead."
)
