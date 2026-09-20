"""Безопасное выполнение SELECT на mock-данных. Только чтение."""

from __future__ import annotations

import re

from pydantic import BaseModel

from app.services.schema import MOCK_TABLES, SCHEMA

FORBIDDEN = ("insert", "update", "delete", "drop", "alter", "create", "truncate", "grant", ";", "--")

_COND_RE = re.compile(r"^\s*([a-z_]+)\s*(>=|<=|<>|!=|=|>|<)\s*('[^']*'|\"[^\"]*\"|[\d.]+)\s*$")


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[dict]
    row_count: int


def _ensure_select_only(sql: str) -> str:
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned[:6].upper() == "SELECT":
        raise ValueError("only SELECT queries are allowed")
    lowered = f" {cleaned.lower()} "
    for word in FORBIDDEN:
        if word in (";", "--"):
            if word in cleaned:
                raise ValueError(f"forbidden token in query: {word!r}")
            continue
        if re.search(rf"\b{word}\b", lowered):
            raise ValueError(f"forbidden keyword in query: {word!r}")
    return cleaned


def _parse_value(raw: str) -> str | float:
    raw = raw.strip()
    if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
        return raw[1:-1]
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"cannot parse value: {raw!r}") from exc


def _match(value: object, op: str, expected: str | float) -> bool:
    if isinstance(expected, str):
        actual_text = str(value)
        if op == "=":
            return actual_text.lower() == expected.lower()
        if op in ("<>", "!="):
            return actual_text.lower() != expected.lower()
        raise ValueError(f"operator {op!r} not supported for strings")
    try:
        actual_num = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"cannot compare {value!r} with {expected!r}") from exc
    if op == "=":
        return actual_num == expected
    if op == ">":
        return actual_num > expected
    if op == "<":
        return actual_num < expected
    if op == ">=":
        return actual_num >= expected
    if op == "<=":
        return actual_num <= expected
    if op in ("<>", "!="):
        return actual_num != expected
    raise ValueError(f"unknown operator: {op!r}")


def execute(sql: str, max_rows: int = 100) -> QueryResult:
    """Выполнить SELECT над mock-таблицами. Детерминировано."""
    cleaned = _ensure_select_only(sql)
    match = re.match(
        r"(?is)^SELECT\s+(?P<cols>[\w\s,*.]+?)\s+FROM\s+(?P<table>\w+)"
        r"(?:\s+WHERE\s+(?P<where>.*?))?(?:\s+ORDER\s+BY\s+(?P<order>\w+)(?:\s+(?P<direction>ASC|DESC))?)?"
        r"(?:\s+LIMIT\s+(?P<limit>\d+))?\s*$",
        cleaned,
    )
    if not match:
        raise ValueError("cannot parse query: only simple SELECT ... FROM ... [WHERE ...] supported")
    table = match.group("table").lower()
    if table not in SCHEMA:
        raise ValueError(f"unknown table: {table!r}")
    raw_cols = [col.strip().lower() for col in match.group("cols").split(",")]
    if raw_cols == ["*"]:
        columns = list(SCHEMA[table])
    else:
        unknown = [col for col in raw_cols if col not in SCHEMA[table]]
        if unknown:
            raise ValueError(f"unknown columns for {table}: {unknown}")
        columns = raw_cols
    rows = list(MOCK_TABLES[table])
    where = match.group("where")
    if where:
        for part in re.split(r"\s+AND\s+", where, flags=re.IGNORECASE):
            cond = _COND_RE.match(part)
            if not cond:
                raise ValueError(f"cannot parse condition: {part!r}")
            column, op, raw = cond.group(1).lower(), cond.group(2), cond.group(3)
            if column not in SCHEMA[table]:
                raise ValueError(f"unknown column in WHERE: {column!r}")
            expected = _parse_value(raw)
            rows = [row for row in rows if _match(row.get(column), op, expected)]
    order = match.group("order")
    if order:
        order = order.lower()
        if order not in SCHEMA[table]:
            raise ValueError(f"unknown column in ORDER BY: {order!r}")
        reverse = (match.group("direction") or "ASC").upper() == "DESC"
        rows.sort(key=lambda row: (row.get(order) is None, row.get(order)), reverse=reverse)
    limit = int(match.group("limit")) if match.group("limit") else max_rows
    rows = rows[: min(limit, max_rows)]
    return QueryResult(
        columns=columns,
        rows=[{col: row.get(col) for col in columns} for row in rows],
        row_count=len(rows),
    )
