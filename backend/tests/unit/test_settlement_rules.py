"""Settlement — domain rules (Sprint 2, Hito 5). Funciones puras, sin DB."""

import pytest

from core.settlement.domain.rules import (
    COUNTRY_TEMPLATES,
    SettlementInvariantError,
    build_checklist_items,
    start_checklist,
    update_item_status,
)
from core.settlement.domain.value_objects import SettlementItemStatus

# ---- build_checklist_items ----


@pytest.mark.parametrize("country", ["Estados Unidos", "Canadá", "Australia", "España"])
def test_build_checklist_items_returns_six_items_per_pilot_country(country):
    items = build_checklist_items(country)
    assert len(items) == 6
    assert [i.sequence for i in items] == list(range(1, 7))
    assert all(i.status == SettlementItemStatus.PENDING for i in items)


def test_build_checklist_items_raises_for_country_outside_pilot_catalog():
    with pytest.raises(SettlementInvariantError):
        build_checklist_items("Francia")


def test_country_templates_cover_exactly_the_four_pilot_countries():
    assert set(COUNTRY_TEMPLATES.keys()) == {"Estados Unidos", "Canadá", "Australia", "España"}


# ---- start_checklist ----


def test_start_checklist_creates_new_checklist_for_case():
    checklist = start_checklist(case_id=5, country="Estados Unidos", existing=None)
    assert checklist.case_id == 5
    assert checklist.country == "Estados Unidos"


def test_start_checklist_raises_if_one_already_exists_for_case():
    existing = start_checklist(case_id=5, country="Estados Unidos", existing=None)
    with pytest.raises(SettlementInvariantError):
        start_checklist(case_id=5, country="Estados Unidos", existing=existing)


# ---- update_item_status ----


def test_update_item_status_updates_matching_item():
    checklist = start_checklist(case_id=5, country="Canadá", existing=None)
    checklist.items = build_checklist_items("Canadá")
    for i, item in enumerate(checklist.items, start=1):
        item.id = i

    update_item_status(checklist, item_id=2, new_status=SettlementItemStatus.DONE)

    updated = next(i for i in checklist.items if i.id == 2)
    assert updated.status == SettlementItemStatus.DONE
    assert updated.updated_at is not None


def test_update_item_status_raises_for_unknown_item_id():
    checklist = start_checklist(case_id=5, country="Canadá", existing=None)
    checklist.items = build_checklist_items("Canadá")
    for i, item in enumerate(checklist.items, start=1):
        item.id = i

    with pytest.raises(SettlementInvariantError):
        update_item_status(checklist, item_id=999, new_status=SettlementItemStatus.DONE)
