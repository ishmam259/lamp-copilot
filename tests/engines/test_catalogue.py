"""Sourced financing catalogue (win plan CORE-14)."""

import json

from app.engines.catalogue import CATALOGUE, HORIZON_DAYS, get_catalogue

PID = "green-life"


def test_every_archetype_cites_a_source():
    rows = json.loads(CATALOGUE.read_text(encoding="utf-8"))["archetypes"]
    assert len(rows) >= 6
    assert all(r["source"].startswith("https://") and r["anchored_on"] for r in rows)


def test_matched_eligible_and_reasons(db):
    c = get_catalogue(db, PID)
    assert (c.need.amount, c.matched, c.horizon_days) == (8_200, 6, HORIZON_DAYS)
    o = {x.key: x for x in c.options}
    # eligible: pays out in time, within limits, price published
    assert o["wallet_nano_loan"].eligible and o["wallet_nano_loan"].cost_of_gap_bdt == 181.97
    assert "personally" in o["wallet_nano_loan"].note
    assert o["mfi_enterprise_loan"].eligible and o["mfi_enterprise_loan"].to_confirm
    # ineligible, each with its reason
    assert "10" in o["cmsme_refinance_wc"].ineligible_reason       # takes 21 days; needed in 10
    assert "10" in o["bank_unsecured_cmsme"].ineligible_reason
    assert "merchant" in o["wallet_pay_later"].ineligible_reason
    assert "isn't published" in o["retailer_platform_credit"].ineligible_reason
    assert c.eligible == sum(x.eligible for x in c.options)
    # eligible first, cheapest first
    costs = [x.cost_of_gap_bdt for x in c.options if x.eligible]
    assert costs == sorted(costs) and c.options[0].eligible


def test_costs_use_one_horizon_and_disclose_the_gap(db):
    o = {x.key: x for x in get_catalogue(db, PID).options}
    b = o["bank_unsecured_cmsme"]
    assert (b.apr_pct, b.amount_financed, b.cost_of_gap_bdt, b.cost_of_gap_pct_of_need) == (13.75, 8_200, 278.01, 3.39)
    assert o["mfi_enterprise_loan"].cost_of_gap_bdt == 404.38


def test_golden_plan_still_holds_against_the_sourced_catalogue(db):
    """If a sourced product ever beats the plan's fallback, this fails on purpose: the team
    then updates the golden numbers everywhere (D-07), never the product's terms."""
    c = get_catalogue(db, PID)
    assert c.plan_fallback_cost_bdt == 181.97
    assert c.plan_holds, (c.cheapest_eligible_cost_bdt, c.plan_fallback_cost_bdt)
