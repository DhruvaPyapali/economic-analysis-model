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

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from display_currency import CURRENCIES, currency_label, format_money
from economics_model import (
    MODEL_CONTINUOUS,
    MODEL_DISCONTINUOUS,
    GrowthMethod,
    SimpleModelInputs,
    run_simple_model,
)


def _pct(x: float) -> float:
    return x / 100.0


def _to_reporting(amount: float, fx_rate: float) -> float:
    """Convert target-currency amount to reporting currency (divide by rate)."""
    if fx_rate <= 0:
        return amount
    return amount / fx_rate


st.set_page_config(page_title="Economic Analysis (Simple)", layout="wide")

st.title("Economic Analysis — Simple model")
st.caption(
    "M&A-style simple path: combine acquirer + target sales, discount target gross profit, quick valuation checks."
)

with st.sidebar:
    st.header("Currency")
    reporting_ccy = st.selectbox(
        "Reporting currency",
        options=list(CURRENCIES.keys()),
        format_func=currency_label,
        index=0,
        key="reporting_ccy",
        help="All outputs and acquirer inputs are shown in this currency.",
    )
    target_other_ccy = st.checkbox(
        "Target amounts entered in another currency",
        value=False,
        key="target_other_ccy",
        help="Convert target revenue, COGS, and EBITDA into reporting currency before the model runs.",
    )
    fx_rate = 1.0
    if target_other_ccy:
        target_ccy_options = [c for c in CURRENCIES.keys() if c != reporting_ccy]
        if not target_ccy_options:
            target_ccy_options = list(CURRENCIES.keys())
        target_ccy = st.selectbox(
            "Target input currency",
            options=target_ccy_options,
            format_func=currency_label,
            key="target_input_ccy",
        )
        fx_rate = st.number_input(
            f"Exchange rate ({target_ccy} per 1 {reporting_ccy})",
            min_value=0.0001,
            value=1.0,
            step=0.01,
            format="%.4f",
            key="fx_rate",
            help=(
                f"How many {target_ccy} equal one {reporting_ccy}. "
                f"Example: if 1 {reporting_ccy} = 0.92 {target_ccy}, enter 0.92."
            ),
        )
        st.caption(
            f"Target figures are converted: "
            f"**{reporting_ccy}** = **{target_ccy}** ÷ {fx_rate:g}."
        )

    st.divider()
    st.header("Valuation model")
    model_kind = st.radio(
        "Growth and risk framework",
        options=["Continuous", "Discontinuous"],
        index=0,
        key="model_kind",
        help=(
            "**Continuous** — single growth path; discount rate = risk-free plus a risk premium. "
            "**Discontinuous** — weighted optimistic / base / pessimistic scenarios; "
            "discount rate = risk-free only."
        ),
    )
    growth_method: GrowthMethod = (
        MODEL_DISCONTINUOUS if model_kind == "Discontinuous" else MODEL_CONTINUOUS
    )
    is_discrete = growth_method == MODEL_DISCONTINUOUS

    risk_free_pct = st.number_input(
        "Risk-free rate",
        min_value=0.0,
        max_value=30.0,
        value=2.78,
        step=0.05,
        format="%.2f",
        key="risk_free_pct",
        help="Annual rate, percent (e.g. 2.78 = 2.78%).",
    )
    risk_free = _pct(risk_free_pct)

    p_opt = 0.0
    p_pess = 0.0
    p_opt_pct = 0
    p_pess_pct = 0

    if is_discrete:
        p_opt_pct = st.slider(
            "Optimistic scenario weight",
            0,
            100,
            0,
            5,
            format="%d%%",
            key="p_opt_pct",
        )
        p_pess_pct = st.slider(
            "Pessimistic scenario weight",
            0,
            100,
            0,
            5,
            format="%d%%",
            key="p_pess_pct",
        )
        p_opt = _pct(float(p_opt_pct))
        p_pess = _pct(float(p_pess_pct))
        sq = max(0.0, 100 - p_opt_pct - p_pess_pct)
        st.caption(f"Base case weight: **{sq:.0f}%** (remainder).")
    else:
        risk_premium_pct = st.slider(
            "Risk premium (added to discount rate)",
            0,
            100,
            0,
            5,
            format="%d%%",
            key="risk_premium_pct",
            help="Continuous model: discount rate = risk-free + this premium (workbook “Other” path).",
        )
        p_opt = _pct(float(risk_premium_pct))

    if is_discrete and p_opt + p_pess > 1.0:
        st.error("Optimistic + pessimistic cannot exceed 100%.")

    margins_same = st.checkbox(
        "Use the same margins in every scenario",
        value=True,
        key="margins_same",
        help="If off, you can type optimistic and pessimistic gross and EBITDA margins below.",
    )

    st.divider()
    st.header("Market multiples")
    pe_ratio = st.number_input(
        "Price ÷ gross profit (year 0)",
        min_value=0.0,
        value=20.0,
        step=0.5,
        key="pe_ratio",
        help="Heuristic price check: multiple × target year-0 gross profit.",
    )
    peg_ratio = st.number_input(
        "PEG multiple",
        min_value=0.0,
        value=2.0,
        step=0.1,
        key="peg_ratio",
        help="Used with weighted sales growth and gross profit in the PEG-style row.",
    )
    ps_ratio = st.number_input(
        "Price ÷ sales",
        min_value=0.0,
        value=4.0,
        step=0.25,
        key="ps_ratio",
        help="Multiple × target revenue.",
    )

ccy_sym = CURRENCIES[reporting_ccy]["symbol"].strip()
money_hint = f"Amounts in {reporting_ccy} ({ccy_sym}) unless noted."

col_a, col_t = st.columns(2)

with col_a:
    st.subheader("Acquirer (buyer)")
    st.caption(f"Most recent year. {money_hint}")
    ar = st.number_input("Revenue", key="ar", min_value=0.0, value=100.0, step=1.0, format="%.0f")
    ac = st.number_input("Cost of goods sold", key="ac", min_value=0.0, value=40.0, step=1.0, format="%.0f")
    ae = st.number_input("EBITDA", key="ae", min_value=0.0, value=25.0, step=1.0, format="%.0f")
    ag_pct = st.number_input(
        "Past revenue growth (per year)",
        key="ag",
        value=3.0,
        step=0.5,
        format="%.1f",
        help="Percent per year for the base case sales path.",
    )
    ag = _pct(ag_pct)
    if is_discrete:
        st.markdown("**Scenario sales growth (per year)**")
        ago_pct = st.number_input(
            "Optimistic", key="ago", value=6.0, step=0.5, format="%.1f", help="Percent per year."
        )
        agp_pct = st.number_input(
            "Pessimistic", key="agp", value=1.0, step=0.5, format="%.1f", help="Percent per year."
        )
        ago, agp = _pct(ago_pct), _pct(agp_pct)
    else:
        ago = agp = 0.0
    if is_discrete and not margins_same:
        st.markdown("**Scenario margins (percent of revenue)**")
        agmo_pct = st.number_input("Optimistic gross margin", key="agmo", value=65.0, step=1.0, format="%.0f")
        agmp_pct = st.number_input("Pessimistic gross margin", key="agmp", value=55.0, step=1.0, format="%.0f")
        aemo_pct = st.number_input("Optimistic EBITDA margin", key="aemo", value=30.0, step=1.0, format="%.0f")
        aemp_pct = st.number_input("Pessimistic EBITDA margin", key="aemp", value=20.0, step=1.0, format="%.0f")
        agmo, agmp = _pct(agmo_pct), _pct(agmp_pct)
        aemo, aemp = _pct(aemo_pct), _pct(aemp_pct)
    else:
        agmo = agmp = aemo = aemp = 0.0

with col_t:
    st.subheader("Target (seller)")
    if target_other_ccy:
        st.caption(
            f"Enter amounts in **{st.session_state.get('target_input_ccy', 'other')}**; "
            f"converted to **{reporting_ccy}** for the model."
        )
    else:
        st.caption(f"Most recent year. {money_hint}")
    tr_raw = st.number_input("Revenue", key="tr", min_value=0.0, value=50.0, step=1.0, format="%.0f")
    tc_raw = st.number_input("Cost of goods sold", key="tc", min_value=0.0, value=20.0, step=1.0, format="%.0f")
    te_raw = st.number_input("EBITDA", key="te", min_value=0.0, value=12.0, step=1.0, format="%.0f")
    tr = _to_reporting(tr_raw, fx_rate) if target_other_ccy else tr_raw
    tc = _to_reporting(tc_raw, fx_rate) if target_other_ccy else tc_raw
    te = _to_reporting(te_raw, fx_rate) if target_other_ccy else te_raw
    if target_other_ccy and fx_rate > 0 and (tr_raw or tc_raw or te_raw):
        st.caption(
            f"In {reporting_ccy}: revenue **{format_money(tr, reporting_ccy)}**, "
            f"COGS **{format_money(tc, reporting_ccy)}**, "
            f"EBITDA **{format_money(te, reporting_ccy)}**."
        )
    tg_pct = st.number_input(
        "Past revenue growth (per year)",
        key="tg",
        value=4.0,
        step=0.5,
        format="%.1f",
        help="Percent per year for the base case sales path.",
    )
    tg = _pct(tg_pct)
    if is_discrete:
        st.markdown("**Scenario sales growth (per year)**")
        tgo_pct = st.number_input(
            "Optimistic", key="tgo", value=8.0, step=0.5, format="%.1f", help="Percent per year."
        )
        tgp_pct = st.number_input(
            "Pessimistic", key="tgp", value=0.0, step=0.5, format="%.1f", help="Percent per year."
        )
        tgo, tgp = _pct(tgo_pct), _pct(tgp_pct)
    else:
        tgo = tgp = 0.0
    if is_discrete and not margins_same:
        st.markdown("**Scenario margins (percent of revenue)**")
        tgmo_pct = st.number_input("Optimistic gross margin", key="tgmo", value=70.0, step=1.0, format="%.0f")
        tgmp_pct = st.number_input("Pessimistic gross margin", key="tgmp", value=50.0, step=1.0, format="%.0f")
        temo_pct = st.number_input("Optimistic EBITDA margin", key="temo", value=32.0, step=1.0, format="%.0f")
        temp_pct = st.number_input("Pessimistic EBITDA margin", key="temp", value=18.0, step=1.0, format="%.0f")
        tgmo, tgmp = _pct(tgmo_pct), _pct(tgmp_pct)
        temo, temp = _pct(temo_pct), _pct(temp_pct)
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

if is_discrete and p_opt + p_pess > 1.0:
    st.stop()

res = run_simple_model(inp)

model_badge = "Discontinuous (weighted scenarios)" if is_discrete else "Continuous (single path)"
st.info(f"**{model_badge}** · Reporting currency: **{reporting_ccy}** ({CURRENCIES[reporting_ccy]['name']})")

mcol1, mcol2, mcol3, mcol4 = st.columns(4)
mcol1.metric("Discount rate", f"{res.discount_rate:.2%}", help="Used for NPV rows.")
mcol2.metric(
    "NPV — 10y target gross profit",
    format_money(res.npv_gross_profit_10y, reporting_ccy),
    help="Present value of years 1–10 gross profit.",
)
mcol3.metric(
    "NPV — terminal-style",
    format_money(res.valuation_terminal_style, reporting_ccy),
    help="Nine years plus a bumped final cash flow, per workbook pattern.",
)
_g2 = res.yoy_revenue_growth[2]
mcol4.metric(
    "Combined sales growth (yr 2)",
    f"{_g2:.1%}" if res.combined_gross_sales[1] > 0 and pd.notna(_g2) else "—",
    help="Year-on-year change in combined sales from year 1 to year 2.",
)

st.subheader("Target price heuristics")
vcol1, vcol2, vcol3 = st.columns(3)
vcol1.metric(
    "Gross-profit multiple",
    format_money(res.price_pe, reporting_ccy),
    help="Multiple × year-0 target gross profit.",
)
vcol2.metric(
    "PEG-style",
    format_money(res.price_peg, reporting_ccy),
    help="Uses weighted sales growth and gross profit.",
)
vcol3.metric(
    "Sales multiple",
    format_money(res.price_ps, reporting_ccy),
    help="Multiple × target revenue.",
)

years = list(range(11))
df = pd.DataFrame(
    {
        "Year": years,
        "Combined sales": res.combined_gross_sales,
        "Combined gross profit": res.combined_gross_profit,
        "Combined gross margin": res.combined_gross_margin,
        "YoY sales growth": res.yoy_revenue_growth,
        "Target gross profit": res.target.gross_profit,
        "Acquirer gross profit": res.acquirer.gross_profit,
    }
)

_chart_fingerprint = hash(
    (
        res.combined_gross_sales.tobytes(),
        res.combined_gross_profit.tobytes(),
        reporting_ccy.encode(),
        growth_method.encode(),
    )
)

st.subheader("Forecast chart")
st.caption(
    f"Lines in **{reporting_ccy}**. They move when you change revenues, COGS, EBITDA, growth rates, "
    f"or (discontinuous) scenario mix. Discount and multiples only change KPIs above—not these lines."
)
fig = go.Figure()
fig.add_trace(go.Scatter(x=years, y=res.combined_gross_sales, name="Combined sales", mode="lines+markers"))
fig.add_trace(go.Scatter(x=years, y=res.combined_gross_profit, name="Combined gross profit", mode="lines+markers"))
fig.update_layout(
    height=420,
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis_title=f"Amount ({reporting_ccy})",
    xaxis_title="Year",
)
st.plotly_chart(fig, use_container_width=True, key=f"forecast_{_chart_fingerprint & 0xFFFFFFFFFFFFFFFF}")

st.subheader("Year-by-year table")
disp = df.copy()
for c in ["Combined sales", "Combined gross profit", "Target gross profit", "Acquirer gross profit"]:
    disp[c] = disp[c].map(lambda x, ccy=reporting_ccy: format_money(x, ccy))
disp["Combined gross margin"] = disp["Combined gross margin"].map(lambda x: f"{x:.1%}")
disp["YoY sales growth"] = disp["YoY sales growth"].map(lambda x: "—" if pd.isna(x) else f"{x:.1%}")
st.dataframe(disp, use_container_width=True, hide_index=True, key=f"table_{_chart_fingerprint & 0xFFFFFFFFFFFFFFFF}")

if is_discrete:
    with st.expander("Derived scenario mix (target)"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Optimistic", f"{res.target.p_opt:.0%}")
        c2.metric("Base", f"{res.target.p_sq:.0%}")
        c3.metric("Pessimistic", f"{res.target.p_pess:.0%}")
        st.caption(
            f"Weighted sales growth **{res.target.w_sales_growth:.2%}/yr**, "
            f"gross margin **{res.target.w_gross_margin:.1%}**, "
            f"EBITDA margin **{res.target.w_ebitda_margin:.1%}**."
        )

st.caption(
    "Terminal NPV uses the Simple target path (the Excel file points that row at the Complex sheet by mistake)."
)
