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

# Excel Dashboard C27 (shared strings 236–237)
DISCRETE_GROWTH_METHOD = "Discrete (Weighted Cash Flows)"
CONTINUOUS_GROWTH_METHOD = "Continuous (Discount Rate Premium)"

try:
    from economics_model import SimpleModelInputs, run_simple_model
except ImportError as _import_err:
    st.set_page_config(page_title="Economic Analysis (Simple)", layout="wide")
    st.error(
        "Failed to load `economics_model.py`. "
        "On Streamlit Cloud, open **Manage app → Reboot app** after a deploy, "
        "or check that `economics_model.py` is in the repo root next to `app.py`."
    )
    st.exception(_import_err)
    st.stop()

# Friendly labels → workbook growth-method values
GROWTH_MODE_LABELS: dict[str, str] = {
    "Discrete — weighted cash flows": DISCRETE_GROWTH_METHOD,
    "Continuous — discount rate premium": CONTINUOUS_GROWTH_METHOD,
}

CURRENCIES: dict[str, dict[str, str]] = {
    "USD — US dollar": {"symbol": "$", "suffix": ""},
    "EUR — euro": {"symbol": "€", "suffix": ""},
    "GBP — British pound": {"symbol": "£", "suffix": ""},
    "CAD — Canadian dollar": {"symbol": "C$", "suffix": ""},
    "AUD — Australian dollar": {"symbol": "A$", "suffix": ""},
    "CHF — Swiss franc": {"symbol": "CHF ", "suffix": ""},
    "JPY — Japanese yen": {"symbol": "¥", "suffix": ""},
    "CNY — Chinese yuan": {"symbol": "¥", "suffix": ""},
    "INR — Indian rupee": {"symbol": "₹", "suffix": ""},
    "None (plain numbers)": {"symbol": "", "suffix": ""},
}


def _pct(x: float) -> float:
    return x / 100.0


def _format_money(value: float, currency_key: str, *, decimals: int = 0) -> str:
    meta = CURRENCIES[currency_key]
    symbol = meta["symbol"]
    if currency_key.startswith("JPY"):
        formatted = f"{value:,.0f}"
    elif decimals == 0:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.{decimals}f}"
    if not symbol:
        return formatted
    if symbol.endswith(" "):
        return f"{symbol}{formatted}{meta['suffix']}"
    return f"{symbol}{formatted}{meta['suffix']}"


st.set_page_config(page_title="Economic Analysis (Simple)", layout="wide")

st.title("Economic Analysis — Simple model")
st.caption("M&A-style simple path: combine acquirer + target sales, discount target gross profit, quick valuation checks.")

with st.expander("ℹ️ About this model — quick reference (from the User Manual)", expanded=False):
    st.markdown(
        """
**Simple Analysis** is a Discounted Cash Flow (DCF) model of a target company. It can either weight
future cash flows by probability for **discrete** outcomes, or account for **continuous** risk via a
premium added to the discount rate. Base-year revenue, COGS, EBITDA, and revenue growth are
required inputs.

| Term | Definition |
|---|---|
| **EBITDA** | Earnings Before Interest, Tax, Depreciation & Amortization — measures operating income while negating aggressive accounting policies. |
| **Risk-Free Rate** | Return on a security with no default risk, typically the 10-year US Treasury bond yield. |
| **Terminal Value** | Future value of a firm assuming sustainable perpetual growth — can also represent a liquidation value. |
| **Time Horizon** | Number of projection periods; only use a horizon where you are comfortable with your estimates. |
| **WACC** | Weighted Average Cost of Capital — discount rate based on a firm's current capital structure. |
| **Discrete risk** | Best for quantifiable single events (e.g. regulatory approval); modelled with probability-weighted optimistic / base / pessimistic scenarios. |
| **Continuous risk** | Ongoing, non-quantifiable risk (e.g. inflation, political risk); modelled by adding a premium to the discount rate. |

*Source: Economic Analysis Model User Manual, Gavin Cochran, University of Washington Bothell (2013).*
        """
    )

with st.sidebar:
    st.header("Display")
    currency_key = st.selectbox(
        "Currency",
        list(CURRENCIES.keys()),
        index=0,
        key="currency_key",
        help="Labels amounts in the UI only — no FX conversion is performed. All inputs should already be in the same currency.",
    )
    currency_meta = CURRENCIES[currency_key]
    money_hint = (
        "All money fields use the same currency (display only — no FX conversion)."
        if currency_meta["symbol"]
        else "Amounts shown without a currency symbol."
    )

    st.divider()
    st.header("Model type")
    mode_label = st.radio(
        "Growth / risk method",
        list(GROWTH_MODE_LABELS.keys()),
        index=1,
        horizontal=True,
        key="growth_mode_label",
        help=(
            "Discrete — risk that is best quantified by single events (e.g. regulatory approval). "
            "Uses probability-weighted cash flows for optimistic, base, and pessimistic scenarios.\n\n"
            "Continuous — ongoing risk that cannot be quantified as a single event (e.g. inflation, political risk). "
            "Accounted for by adding a premium to the risk-free discount rate."
        ),
    )
    growth_method = GROWTH_MODE_LABELS[mode_label]
    discrete_mode = growth_method == DISCRETE_GROWTH_METHOD

    risk_free_pct = st.number_input(
        "Risk-free rate",
        min_value=0.0,
        max_value=30.0,
        value=2.78,
        step=0.05,
        format="%.2f",
        key="risk_free_pct",
        help=(
            "Annual return on a security with no default risk — typically the 10-year US Treasury yield. "
            "A historical rate may be more sensible than the current rate depending on market conditions. "
            "Enter as a percentage (e.g. 2.78 = 2.78%)."
        ),
    )
    risk_free = _pct(risk_free_pct)

    if discrete_mode:
        p_opt_pct = st.slider(
            "Optimistic scenario weight",
            0,
            100,
            0,
            5,
            format="%d%%",
            key="p_opt_pct",
            help=(
                "Probability of the optimistic scenario. Both inputs should be reasonable — "
                "optimistic + pessimistic must stay at or below 100% (the remainder is the base case). "
                "Remember that growth can be negative in a pessimistic scenario."
            ),
        )
        p_pess_pct = st.slider(
            "Pessimistic scenario weight",
            0,
            100,
            0,
            5,
            format="%d%%",
            key="p_pess_pct",
            help=(
                "Probability of the pessimistic scenario. Growth can be negative here. "
                "Optimistic + pessimistic must stay at or below 100% — the remainder becomes the base case weight."
            ),
        )
        sq = max(0.0, 100 - p_opt_pct - p_pess_pct)
        st.caption(f"Base case weight: **{sq:.0f}%** (remainder).")
    else:
        p_opt_pct = st.slider(
            "Discount rate premium (optimistic)",
            0,
            100,
            0,
            5,
            format="%d%%",
            key="p_opt_pct",
            help=(
                "Risk premium added to the risk-free rate to form the discount rate (Continuous mode). "
                "While there is no single preferred method to calculate this, the premium should reflect the "
                "firm's specific risk — emerging-market companies, for example, should carry a higher premium "
                "than those in developed markets."
            ),
        )
        p_pess_pct = 0
        st.caption("Pessimistic weight is not used in **Continuous** mode.")

    p_opt = _pct(float(p_opt_pct))
    p_pess = _pct(float(p_pess_pct))

    if discrete_mode and p_opt + p_pess > 1.0:
        st.error("Optimistic + pessimistic cannot exceed 100%.")
    margins_same = st.checkbox(
        "Use the same margins in every scenario",
        value=True,
        key="margins_same",
        help=(
            "When unchecked, you can enter distinct optimistic and pessimistic gross and EBITDA margins "
            "for both companies. Use this when you expect margins to differ meaningfully across scenarios."
        ),
    )

    st.divider()
    st.header("Market multiples")
    pe_ratio = st.number_input(
        "Price ÷ gross profit (year 0)",
        min_value=0.0,
        value=20.0,
        step=0.5,
        key="pe_ratio",
        help=(
            "A quick valuation check: this multiple times the target's year-0 gross profit. "
            "Some markets (especially private equity) value firms on a multiple of earnings or gross profit."
        ),
    )
    peg_ratio = st.number_input(
        "PEG multiple",
        min_value=0.0,
        value=2.0,
        step=0.1,
        key="peg_ratio",
        help=(
            "PEG-style heuristic: combines this multiple with the probability-weighted sales growth rate "
            "and the target's gross profit to estimate a growth-adjusted price."
        ),
    )
    ps_ratio = st.number_input(
        "Price ÷ sales",
        min_value=0.0,
        value=4.0,
        step=0.25,
        key="ps_ratio",
        help="Price-to-sales heuristic: this multiple times the target's base-year revenue.",
    )

col_a, col_t = st.columns(2)

with col_a:
    st.subheader("Acquirer (buyer)")
    st.caption(f"Base year; {money_hint}")
    ar = st.number_input(
        "Revenue", key="ar", min_value=0.0, value=100.0, step=1.0, format="%.0f",
        help=(
            "Base-year revenue — the starting point for future projections. "
            "'Base year' doesn't have to be the most recent year; choose the year most representative of firm performance."
        ),
    )
    ac = st.number_input(
        "Cost of goods sold", key="ac", min_value=0.0, value=40.0, step=1.0, format="%.0f",
        help="Direct costs of producing goods or services. Gross profit = Revenue − COGS.",
    )
    ae = st.number_input(
        "EBITDA", key="ae", min_value=0.0, value=25.0, step=1.0, format="%.0f",
        help=(
            "Earnings Before Interest, Tax, Depreciation & Amortization. "
            "Measures operating income while negating aggressive accounting policies. "
            "Used as an input for EBITDA-based valuation checks."
        ),
    )
    ag_pct = st.number_input(
        "Past revenue growth (per year)",
        key="ag",
        value=3.0,
        step=0.5,
        format="%.1f",
        help=(
            "Historical revenue growth rate used as the base-case sales path. "
            "Only include periods that reflect the current state of the firm — "
            "exclude periods prior to major divestitures or business-model changes."
        ),
    )
    ag = _pct(ag_pct)
    st.markdown("**Scenario sales growth (per year)**")
    ago_pct = st.number_input(
        "Optimistic", key="ago", value=6.0, step=0.5, format="%.1f",
        help="Expected annual revenue growth under the optimistic scenario. Should be a plausible upside estimate.",
    )
    agp_pct = st.number_input(
        "Pessimistic", key="agp", value=1.0, step=0.5, format="%.1f",
        help="Expected annual revenue growth under the pessimistic scenario. Can be negative.",
    )
    ago, agp = _pct(ago_pct), _pct(agp_pct)
    if not margins_same:
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
    st.caption(f"Base year; {money_hint}")
    tr = st.number_input(
        "Revenue", key="tr", min_value=0.0, value=50.0, step=1.0, format="%.0f",
        help=(
            "Base-year revenue — the starting point for future projections. "
            "'Base year' doesn't have to be the most recent year; choose the year most representative of firm performance."
        ),
    )
    tc = st.number_input(
        "Cost of goods sold", key="tc", min_value=0.0, value=20.0, step=1.0, format="%.0f",
        help="Direct costs of producing goods or services. Gross profit = Revenue − COGS.",
    )
    te = st.number_input(
        "EBITDA", key="te", min_value=0.0, value=12.0, step=1.0, format="%.0f",
        help=(
            "Earnings Before Interest, Tax, Depreciation & Amortization. "
            "Measures operating income while negating aggressive accounting policies. "
            "Used as an input for EBITDA-based valuation checks."
        ),
    )
    tg_pct = st.number_input(
        "Past revenue growth (per year)",
        key="tg",
        value=4.0,
        step=0.5,
        format="%.1f",
        help=(
            "Historical revenue growth rate used as the base-case sales path. "
            "Only include periods that reflect the current state of the firm — "
            "exclude periods prior to major divestitures or business-model changes."
        ),
    )
    tg = _pct(tg_pct)
    st.markdown("**Scenario sales growth (per year)**")
    tgo_pct = st.number_input(
        "Optimistic", key="tgo", value=8.0, step=0.5, format="%.1f",
        help="Expected annual revenue growth under the optimistic scenario. Should be a plausible upside estimate.",
    )
    tgp_pct = st.number_input(
        "Pessimistic", key="tgp", value=0.0, step=0.5, format="%.1f",
        help="Expected annual revenue growth under the pessimistic scenario. Can be negative.",
    )
    tgo, tgp = _pct(tgo_pct), _pct(tgp_pct)
    if not margins_same:
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

if discrete_mode and p_opt + p_pess > 1.0:
    st.stop()

res = run_simple_model(inp)

mcol1, mcol2, mcol3, mcol4 = st.columns(4)
mcol1.metric(
    "Discount rate",
    f"{res.discount_rate:.2%}",
    help=(
        "The rate used to discount future cash flows to present value. "
        "In Discrete mode this equals the risk-free rate; in Continuous mode the risk premium is added. "
        "Remember that while Treasury rates are a good proxy, a historical rate may be more appropriate "
        "depending on current market conditions."
    ),
)
mcol2.metric(
    "NPV — 10y target gross profit",
    _format_money(res.npv_gross_profit_10y, currency_key),
    help=(
        "Net Present Value of the target's projected gross profit over years 1–10, "
        "discounted at the current discount rate. This is the core DCF valuation output."
    ),
)
mcol3.metric(
    "NPV — terminal-style",
    _format_money(res.valuation_terminal_style, currency_key),
    help=(
        "DCF over nine years with a bumped final cash flow approximating terminal value. "
        "Terminal value represents the present value of the firm assuming sustainable perpetual growth — "
        "it can also be interpreted as a future liquidation value."
    ),
)
_g2 = res.yoy_revenue_growth[2]
mcol4.metric(
    "Combined sales growth (yr 2)",
    f"{_g2:.1%}" if res.combined_gross_sales[1] > 0 and pd.notna(_g2) else "—",
    help=(
        "Year-on-year change in combined (acquirer + target) sales from year 1 to year 2. "
        "Useful for quickly assessing the combined firm's near-term growth trajectory post-acquisition."
    ),
)

st.subheader("Target price heuristics")
vcol1, vcol2, vcol3 = st.columns(3)
vcol1.metric(
    "Gross-profit multiple",
    _format_money(res.price_pe, currency_key),
    help=(
        "Heuristic price estimate: the gross-profit multiple × target's year-0 gross profit. "
        "Some investment markets (especially private equity) value firms on a multiple of earnings or gross profit."
    ),
)
vcol2.metric(
    "PEG-style",
    _format_money(res.price_peg, currency_key),
    help=(
        "Growth-adjusted price estimate using the PEG multiple, probability-weighted sales growth, "
        "and the target's gross profit. Useful for comparing firms with different growth profiles."
    ),
)
vcol3.metric(
    "Sales multiple",
    _format_money(res.price_ps, currency_key),
    help="Heuristic price estimate: the price-to-sales multiple × target's base-year revenue.",
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

# Bust Plotly embed cache when series change (some hosts/browsers reuse the old figure).
_chart_fingerprint = hash(
    (
        res.combined_gross_sales.tobytes(),
        res.combined_gross_profit.tobytes(),
    )
)

st.subheader("Forecast chart")
st.caption(
    "Lines move when you change **revenues, COGS, EBITDA, growth rates**, or **weighted** scenario mix. "
    "**Discount** and **multiples** only change the KPIs and price heuristics above—not these lines."
)

display_years = st.slider(
    "Years to display",
    min_value=1,
    max_value=10,
    value=10,
    step=1,
    key="display_years",
    help=(
        "Choose how many projection years to show in the chart and table (year 0 is always shown). "
        "Per the user manual, only use a time horizon where you are comfortable with your estimates — "
        "if reliable estimates can only be made for five years, a horizon of ten would be inappropriate."
    ),
)
_display_idx = display_years + 1  # include year 0

years_disp = years[:_display_idx]
sales_disp = res.combined_gross_sales[:_display_idx]
profit_disp = res.combined_gross_profit[:_display_idx]

fig = go.Figure()
fig.add_trace(go.Scatter(x=years_disp, y=sales_disp, name="Combined sales", mode="lines+markers"))
fig.add_trace(go.Scatter(x=years_disp, y=profit_disp, name="Combined gross profit", mode="lines+markers"))
fig.update_layout(
    height=440,
    margin=dict(l=10, r=10, t=20, b=60),
    legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
    yaxis_title=currency_key.split(" — ")[0] if currency_meta["symbol"] else "Amount (no currency symbol)",
    xaxis_title="Year",
)
st.plotly_chart(fig, use_container_width=True, key=f"forecast_{_chart_fingerprint & 0xFFFFFFFFFFFFFFFF}_{display_years}")

st.subheader("Year-by-year table")
disp = df.iloc[:_display_idx].copy()
for c in ["Combined sales", "Combined gross profit", "Target gross profit", "Acquirer gross profit"]:
    disp[c] = disp[c].map(lambda x, ck=currency_key: _format_money(float(x), ck, decimals=2))
disp["Combined gross margin"] = disp["Combined gross margin"].map(lambda x: f"{x:.1%}")
disp["YoY sales growth"] = disp["YoY sales growth"].map(lambda x: "—" if pd.isna(x) else f"{x:.1%}")
st.dataframe(disp, use_container_width=True, hide_index=True, key=f"table_{_chart_fingerprint & 0xFFFFFFFFFFFFFFFF}")

with st.expander("Derived scenario mix (target)", expanded=discrete_mode):
    c1, c2, c3 = st.columns(3)
    c1.metric("Optimistic", f"{res.target.p_opt:.0%}")
    c2.metric("Base", f"{res.target.p_sq:.0%}")
    c3.metric("Pessimistic", f"{res.target.p_pess:.0%}")
    st.caption(
        f"Weighted sales growth **{res.target.w_sales_growth:.2%}/yr**, "
        f"gross margin **{res.target.w_gross_margin:.1%}**, EBITDA margin **{res.target.w_ebitda_margin:.1%}**."
    )

