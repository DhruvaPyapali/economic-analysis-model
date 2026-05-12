"""
Simple-path economics from `EconomicAnalysisModel-1.xlsm`
(Combined Company Value-Simple + Variables *-Simple sheets).

Excel NPV semantics: NPV(rate, v1..vn) discounts the first cash flow by (1+r)^1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

GrowthMethod = Literal["Discrete (Weighted Cash Flows)", "Other"]


def excel_npv(discount_rate: float, cashflows: list[float]) -> float:
    """Match Excel NPV: sum(cf_i / (1+r)^i) for i = 1..len(cf)."""
    if discount_rate <= -1:
        return float("nan")
    r = discount_rate
    return float(sum(cf / (1 + r) ** (i + 1) for i, cf in enumerate(cashflows)))


@dataclass
class SimpleModelInputs:
    # Dashboard-style fields referenced by the Simple sheets
    time_horizon_years: int = 10
    growth_method: GrowthMethod = "Other"
    risk_free_rate: float = 0.0278
    optimistic_probability: float = 0.0
    pessimistic_probability: float = 0.0
    margins_same_each_scenario: bool = True

    acquirer_revenue: float = 0.0
    acquirer_cogs: float = 0.0
    acquirer_ebitda: float = 0.0
    acquirer_hist_revenue_growth: float = 0.0
    acquirer_opt_sales_growth: float = 0.0
    acquirer_pess_sales_growth: float = 0.0
    acquirer_opt_gross_margin: float = 0.0
    acquirer_pess_gross_margin: float = 0.0
    acquirer_opt_ebitda_margin: float = 0.0
    acquirer_pess_ebitda_margin: float = 0.0

    target_revenue: float = 0.0
    target_cogs: float = 0.0
    target_ebitda: float = 0.0
    target_hist_revenue_growth: float = 0.0
    target_opt_sales_growth: float = 0.0
    target_pess_sales_growth: float = 0.0
    target_opt_gross_margin: float = 0.0
    target_pess_gross_margin: float = 0.0
    target_opt_ebitda_margin: float = 0.0
    target_pess_ebitda_margin: float = 0.0

    # Valuation knobs on Combined Company Value-Simple
    pe_ratio: float = 20.0
    peg_ratio: float = 2.0
    ps_ratio: float = 4.0


@dataclass
class EntityProjection:
    gross_sales: np.ndarray
    gross_profit: np.ndarray
    ebitda: np.ndarray
    p_opt: float
    p_sq: float
    p_pess: float
    w_sales_growth: float
    w_gross_margin: float
    w_ebitda_margin: float


@dataclass
class SimpleModelResult:
    acquirer: EntityProjection
    target: EntityProjection
    combined_gross_sales: np.ndarray
    combined_gross_profit: np.ndarray
    combined_gross_margin: np.ndarray
    yoy_revenue_growth: np.ndarray
    discount_rate: float
    npv_gross_profit_10y: float
    valuation_npv_simple: float
    valuation_terminal_style: float
    price_pe: float
    price_peg: float
    price_ps: float


def _scenario_probs(method: GrowthMethod, p_opt: float, p_pess: float) -> tuple[float, float, float]:
    discrete = method == "Discrete (Weighted Cash Flows)"
    po = p_opt if discrete else 0.0
    pp = p_pess if discrete else 0.0
    ps = 1.0 - po - pp
    return po, max(ps, 0.0), pp


def _discount_rate(inp: SimpleModelInputs) -> float:
    # =IF(C27="Discrete...", C28, C28+C29)
    if inp.growth_method == "Discrete (Weighted Cash Flows)":
        return inp.risk_free_rate
    return inp.risk_free_rate + inp.optimistic_probability


def _entity_projection(
    revenue: float,
    cogs: float,
    ebitda: float,
    hist_growth: float,
    method: GrowthMethod,
    margins_same: bool,
    p_opt: float,
    p_sq: float,
    p_pess: float,
    opt_g: float,
    pess_g: float,
    opt_gm: float,
    pess_gm: float,
    opt_em: float,
    pess_em: float,
    base_gross_margin: float,
    base_ebitda_margin: float,
    *,
    ebitda_year0_weighted: bool,
) -> EntityProjection:
    g_opt = opt_g
    g_pess = pess_g
    g_sq = hist_growth

    if margins_same:
        gm_opt = gm_sq = gm_pess = base_gross_margin
        em_opt = em_sq = em_pess = base_ebitda_margin
    else:
        gm_opt, gm_pess = opt_gm, pess_gm
        em_opt, em_pess = opt_em, pess_em
        gm_sq, em_sq = base_gross_margin, base_ebitda_margin

    w_g = p_opt * g_opt + p_sq * g_sq + p_pess * g_pess
    w_gm = p_opt * gm_opt + p_sq * gm_sq + p_pess * gm_pess
    w_em = p_opt * em_opt + p_sq * em_sq + p_pess * em_pess

    n = 11
    sales = np.zeros(n)
    gp = np.zeros(n)
    eb = np.zeros(n)
    sales[0] = revenue
    gp[0] = sales[0] * base_gross_margin
    eb[0] = sales[0] * (w_em if ebitda_year0_weighted else base_ebitda_margin)
    for t in range(1, n):
        sales[t] = sales[t - 1] * (1.0 + w_g)
        gp[t] = sales[t] * w_gm
        eb[t] = sales[t] * w_em

    return EntityProjection(
        gross_sales=sales,
        gross_profit=gp,
        ebitda=eb,
        p_opt=p_opt,
        p_sq=p_sq,
        p_pess=p_pess,
        w_sales_growth=w_g,
        w_gross_margin=w_gm,
        w_ebitda_margin=w_em,
    )


def run_simple_model(inp: SimpleModelInputs) -> SimpleModelResult:
    if inp.acquirer_revenue == 0:
        base_gm_a = 0.0
        base_em_a = 0.0
    else:
        base_gm_a = (inp.acquirer_revenue - inp.acquirer_cogs) / inp.acquirer_revenue
        base_em_a = inp.acquirer_ebitda / inp.acquirer_revenue

    if inp.target_revenue == 0:
        base_gm_t = 0.0
        base_em_t = 0.0
    else:
        base_gm_t = (inp.target_revenue - inp.target_cogs) / inp.target_revenue
        base_em_t = inp.target_ebitda / inp.target_revenue

    po, ps, pp = _scenario_probs(inp.growth_method, inp.optimistic_probability, inp.pessimistic_probability)

    acquirer = _entity_projection(
        inp.acquirer_revenue,
        inp.acquirer_cogs,
        inp.acquirer_ebitda,
        inp.acquirer_hist_revenue_growth,
        inp.growth_method,
        inp.margins_same_each_scenario,
        po,
        ps,
        pp,
        inp.acquirer_opt_sales_growth,
        inp.acquirer_pess_sales_growth,
        inp.acquirer_opt_gross_margin,
        inp.acquirer_pess_gross_margin,
        inp.acquirer_opt_ebitda_margin,
        inp.acquirer_pess_ebitda_margin,
        base_gm_a,
        base_em_a,
        ebitda_year0_weighted=True,
    )

    target = _entity_projection(
        inp.target_revenue,
        inp.target_cogs,
        inp.target_ebitda,
        inp.target_hist_revenue_growth,
        inp.growth_method,
        inp.margins_same_each_scenario,
        po,
        ps,
        pp,
        inp.target_opt_sales_growth,
        inp.target_pess_sales_growth,
        inp.target_opt_gross_margin,
        inp.target_pess_gross_margin,
        inp.target_opt_ebitda_margin,
        inp.target_pess_ebitda_margin,
        base_gm_t,
        base_em_t,
        ebitda_year0_weighted=False,
    )

    c_sales = acquirer.gross_sales + target.gross_sales
    c_gp = acquirer.gross_profit + target.gross_profit
    with np.errstate(divide="ignore", invalid="ignore"):
        c_gm = np.where(c_sales != 0, c_gp / c_sales, 0.0)

    yoy = np.zeros_like(c_sales)
    with np.errstate(divide="ignore", invalid="ignore"):
        yoy[1:] = (c_sales[1:] - c_sales[:-1]) / np.where(c_sales[:-1] != 0, c_sales[:-1], np.nan)

    d = _discount_rate(inp)
    tgt_gp = target.gross_profit
    cf_1_10 = [float(x) for x in tgt_gp[1:11]]
    npv_gp = excel_npv(d, cf_1_10)
    val_simple = npv_gp

    # Workbook B25 points at Target-Complex; here we keep structure but use Simple target path.
    cf_term = [float(x) for x in tgt_gp[1:10]] + [float(tgt_gp[10]) + val_simple]
    val_terminal = excel_npv(d, cf_term)

    t_gp0 = float(target.gross_profit[0])
    t_sales_growth = float(target.w_sales_growth)
    price_pe = t_gp0 * inp.pe_ratio
    price_peg = (inp.peg_ratio * (t_sales_growth * 100.0)) * t_gp0
    price_ps = inp.target_revenue * inp.ps_ratio

    return SimpleModelResult(
        acquirer=acquirer,
        target=target,
        combined_gross_sales=c_sales,
        combined_gross_profit=c_gp,
        combined_gross_margin=c_gm,
        yoy_revenue_growth=yoy,
        discount_rate=d,
        npv_gross_profit_10y=npv_gp,
        valuation_npv_simple=val_simple,
        valuation_terminal_style=val_terminal,
        price_pe=price_pe,
        price_peg=price_peg,
        price_ps=price_ps,
    )
