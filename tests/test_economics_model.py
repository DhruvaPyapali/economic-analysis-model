import math

import pytest

from economics_model import SimpleModelInputs, excel_npv, normalize_growth_method, run_simple_model


def base_inputs(**overrides):
    defaults = dict(
        growth_method="Continuous (Discount Rate Premium)",
        risk_free_rate=0.03,
        optimistic_probability=0.10,
        pessimistic_probability=0.20,
        margins_same_each_scenario=True,
        acquirer_revenue=100.0,
        acquirer_cogs=40.0,
        acquirer_ebitda=25.0,
        acquirer_hist_revenue_growth=0.03,
        acquirer_opt_sales_growth=0.06,
        acquirer_pess_sales_growth=0.01,
        acquirer_opt_gross_margin=0.65,
        acquirer_pess_gross_margin=0.55,
        acquirer_opt_ebitda_margin=0.30,
        acquirer_pess_ebitda_margin=0.20,
        target_revenue=50.0,
        target_cogs=20.0,
        target_ebitda=12.0,
        target_hist_revenue_growth=0.04,
        target_opt_sales_growth=0.08,
        target_pess_sales_growth=0.00,
        target_opt_gross_margin=0.70,
        target_pess_gross_margin=0.50,
        target_opt_ebitda_margin=0.32,
        target_pess_ebitda_margin=0.18,
        pe_ratio=20.0,
        peg_ratio=2.0,
        ps_ratio=4.0,
    )
    defaults.update(overrides)
    return SimpleModelInputs(**defaults)


def test_excel_npv_matches_manual_discounting():
    cashflows = [100.0, 100.0, 100.0]
    rate = 0.1
    expected = 100 / 1.1 + 100 / (1.1**2) + 100 / (1.1**3)
    assert excel_npv(rate, cashflows) == pytest.approx(expected)


def test_legacy_other_alias_maps_to_continuous():
    assert normalize_growth_method("Other") == "Continuous (Discount Rate Premium)"


def test_discount_rate_rule_matches_growth_method():
    continuous = run_simple_model(
        base_inputs(growth_method="Continuous (Discount Rate Premium)", risk_free_rate=0.03, optimistic_probability=0.07)
    )
    discrete = run_simple_model(
        base_inputs(
            growth_method="Discrete (Weighted Cash Flows)",
            risk_free_rate=0.03,
            optimistic_probability=0.07,
        )
    )
    assert continuous.discount_rate == pytest.approx(0.10)
    assert discrete.discount_rate == pytest.approx(0.03)


def test_discrete_weighted_growth_and_probabilities():
    inp = base_inputs(
        growth_method="Discrete (Weighted Cash Flows)",
        optimistic_probability=0.25,
        pessimistic_probability=0.15,
        target_hist_revenue_growth=0.04,
        target_opt_sales_growth=0.12,
        target_pess_sales_growth=-0.02,
    )
    res = run_simple_model(inp)
    expected_status_quo = 0.60
    expected_weighted_growth = (0.25 * 0.12) + (expected_status_quo * 0.04) + (0.15 * -0.02)

    assert res.target.p_opt == pytest.approx(0.25)
    assert res.target.p_sq == pytest.approx(expected_status_quo)
    assert res.target.p_pess == pytest.approx(0.15)
    assert res.target.w_sales_growth == pytest.approx(expected_weighted_growth)


def test_higher_discount_rate_reduces_npv():
    low_discount = run_simple_model(
        base_inputs(growth_method="Continuous (Discount Rate Premium)", risk_free_rate=0.01, optimistic_probability=0.02)
    )
    high_discount = run_simple_model(
        base_inputs(growth_method="Continuous (Discount Rate Premium)", risk_free_rate=0.08, optimistic_probability=0.12)
    )
    assert high_discount.discount_rate > low_discount.discount_rate
    assert high_discount.npv_gross_profit_10y < low_discount.npv_gross_profit_10y


def test_zero_input_case_stays_finite_or_nan_only_for_yoy():
    res = run_simple_model(SimpleModelInputs())
    assert res.valuation_npv_simple == pytest.approx(0.0)
    assert res.price_pe == pytest.approx(0.0)
    assert res.price_peg == pytest.approx(0.0)
    assert res.price_ps == pytest.approx(0.0)
    assert math.isnan(res.yoy_revenue_growth[1])
