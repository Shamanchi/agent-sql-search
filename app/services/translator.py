"""Эвристический перевод вопроса в SELECT. Без сети."""

from __future__ import annotations

import re

from pydantic import BaseModel

from app.services.schema import SCHEMA

_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)")


class Translation(BaseModel):
    question: str
    sql: str
    table: str
    confidence: float


def _detect_table(question: str) -> str:
    lowered = question.lower()
    for table in ("users", "orders", "products"):
        singular = table[:-1]
        if table in lowered or singular in lowered:
            return table
    raise ValueError("cannot detect table: mention users, orders or products")


def _detect_columns(question: str, table: str) -> list[str]:
    words = set(re.findall(r"[a-z_]+", question.lower()))
    columns = [col for col in SCHEMA[table] if col in words]
    if "name" in words and "name" not in columns and "name" in SCHEMA[table]:
        columns.append("name")
    if not columns:
        return ["*"] if "all" in words or "everything" in words else _default_columns(table)
    # Стабильный порядок — как в схеме.
    return [col for col in SCHEMA[table] if col in columns]


def _default_columns(table: str) -> list[str]:
    defaults = {"users": ["name", "age"], "orders": ["id", "total", "status"], "products": ["name", "price"]}
    return defaults.get(table, ["*"])


def _detect_conditions(question: str, table: str) -> list[str]:
    lowered = question.lower()
    conditions: list[str] = []
    columns = set(SCHEMA[table])

    if table == "users":
        match = re.search(r"older than\s+(\d+)", lowered)
        if match:
            conditions.append(f"age > {match.group(1)}")
        match = re.search(r"younger than\s+(\d+)", lowered)
        if match:
            conditions.append(f"age < {match.group(1)}")
        match = re.search(r"from\s+([a-z]+)", lowered)
        if match and "city" in columns:
            conditions.append(f"city = '{match.group(1).title()}'")
    if table == "orders":
        match = re.search(r"(?:over|above|greater than)\s+(\d+(?:\.\d+)?)", lowered)
        if match:
            conditions.append(f"total > {match.group(1)}")
        for status in ("paid", "pending", "cancelled"):
            if status in lowered:
                conditions.append(f"status = '{status}'")
                break
    if table == "products":
        match = re.search(r"(?:over|above|greater than|expensive than)\s+(\d+(?:\.\d+)?)", lowered)
        if match:
            conditions.append(f"price > {match.group(1)}")
        match = re.search(r"(?:under|below|cheaper than)\s+(\d+(?:\.\d+)?)", lowered)
        if match:
            conditions.append(f"price < {match.group(1)}")
        if "out of stock" in lowered:
            conditions.append("stock = 0")
        elif "in stock" in lowered:
            conditions.append("stock > 0")
    return conditions


def translate(question: str, default_limit: int = 50) -> Translation:
    """Построить SELECT по вопросу. Детерминировано."""
    if not question or not question.strip():
        raise ValueError("question must not be empty")
    cleaned = question.strip()
    table = _detect_table(cleaned)
    columns = _detect_columns(cleaned, table)
    conditions = _detect_conditions(cleaned, table)
    sql = f"SELECT {', '.join(columns)} FROM {table}"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += f" LIMIT {default_limit}"
    confidence = 0.9 if conditions else 0.6
    if columns == ["*"]:
        confidence = round(confidence - 0.05, 2)
    return Translation(question=cleaned, sql=sql, table=table, confidence=confidence)
