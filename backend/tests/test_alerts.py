import pytest

from app.engine.alerts import AlertChecker, AlertStore, is_met, normalize_symbol, sqlite_path


def test_is_met():
    assert is_met("above", 100, 100)
    assert is_met("above", 100, 101)
    assert not is_met("above", 100, 99.95)
    assert is_met("below", 100, 100)
    assert not is_met("below", 100, 100.05)


def test_normalize_symbol():
    assert normalize_symbol(" reliance ") == "NSE:RELIANCE"
    assert normalize_symbol("bse:tcs") == "BSE:TCS"


def test_store_add_list_delete():
    store = AlertStore()
    alert = store.add("infy", "below", 1400)
    assert alert.symbol == "NSE:INFY" and alert.status == "active"
    assert [a.id for a in store.active()] == [alert.id]
    assert store.active_symbols() == {"NSE:INFY"}
    assert store.delete(alert.id)
    assert not store.delete(alert.id)
    assert store.active() == []


def test_store_rejects_unknown_condition():
    with pytest.raises(ValueError):
        AlertStore().add("INFY", "crosses", 1400)


def test_store_persists_to_file(tmp_path):
    path = sqlite_path(f"sqlite:///{tmp_path}/nested/algo.db")
    AlertStore(path).add("TCS", "above", 4000)
    assert [a.symbol for a in AlertStore(path).active()] == ["NSE:TCS"]


def test_checker_fires_once_when_condition_met():
    store = AlertStore()
    above = store.add("RELIANCE", "above", 3000)
    below = store.add("RELIANCE", "below", 2900)
    checker = AlertChecker(store)

    assert checker.on_tick("NSE:RELIANCE", 2950) == []
    fired = checker.on_tick("NSE:RELIANCE", 3004.5)
    assert [a.id for a in fired] == [above.id]
    assert fired[0].status == "triggered" and fired[0].triggered_price == 3004.5

    # Already triggered: no repeat while price stays above.
    assert checker.on_tick("NSE:RELIANCE", 3010) == []
    assert [a.id for a in store.active()] == [below.id]


def test_checker_ignores_other_symbols():
    store = AlertStore()
    store.add("INFY", "above", 1)
    assert AlertChecker(store).on_tick("NSE:TCS", 5000) == []
