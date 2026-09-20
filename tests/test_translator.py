"""Unit-тесты перевода и исполнителя: без сети, детерминированы."""

import pytest

from app.services.executor import execute
from app.services.translator import translate


def test_translate_users_older() -> None:
    result = translate("show users older than 30")
    assert result.sql == "SELECT name, age FROM users WHERE age > 30 LIMIT 50"
    assert result.table == "users"
    assert result.confidence == 0.9


def test_translate_orders_paid() -> None:
    result = translate("list paid orders over 100")
    assert result.sql == "SELECT id, total, status FROM orders WHERE total > 100 AND status = 'paid' LIMIT 50"


def test_translate_products_stock() -> None:
    result = translate("products out of stock")
    assert "stock = 0" in result.sql
    assert result.table == "products"


def test_translate_unknown_table() -> None:
    with pytest.raises(ValueError):
        translate("show me the weather")


def test_execute_filters_rows() -> None:
    result = execute("SELECT name, age FROM users WHERE age > 30")
    assert result.columns == ["name", "age"]
    assert [row["name"] for row in result.rows] == ["Alice", "Carol"]
    assert result.row_count == 2


def test_execute_rejects_writes() -> None:
    for sql in [
        "DELETE FROM users",
        "UPDATE users SET age = 1",
        "DROP TABLE users",
        "SELECT * FROM users; DROP TABLE users",
    ]:
        with pytest.raises(ValueError):
            execute(sql)


def test_execute_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        execute("SELECT * FROM ghosts")
    with pytest.raises(ValueError):
        execute("SELECT nope FROM users")
