from display_currency import format_money


def test_format_money_usd():
    assert format_money(1_234_567.89, "USD") == "$1,234,568"


def test_format_money_jpy_no_decimals():
    assert format_money(1234.7, "JPY") == "¥1,235"


def test_format_money_compact():
    assert format_money(2_500_000, "USD", compact=True) == "$2.50M"
