"""Mock-схема и данные: офлайн-фикстуры без сети."""

from __future__ import annotations

SCHEMA: dict[str, list[str]] = {
    "users": ["id", "name", "age", "city"],
    "orders": ["id", "user_id", "total", "status"],
    "products": ["id", "name", "price", "stock"],
}

MOCK_TABLES: dict[str, list[dict]] = {
    "users": [
        {"id": 1, "name": "Alice", "age": 34, "city": "Berlin"},
        {"id": 2, "name": "Bob", "age": 28, "city": "Paris"},
        {"id": 3, "name": "Carol", "age": 41, "city": "Berlin"},
        {"id": 4, "name": "Dave", "age": 22, "city": "Madrid"},
    ],
    "orders": [
        {"id": 1, "user_id": 1, "total": 120.5, "status": "paid"},
        {"id": 2, "user_id": 2, "total": 45.0, "status": "pending"},
        {"id": 3, "user_id": 1, "total": 320.0, "status": "paid"},
        {"id": 4, "user_id": 3, "total": 15.99, "status": "cancelled"},
    ],
    "products": [
        {"id": 1, "name": "Keyboard", "price": 79.99, "stock": 12},
        {"id": 2, "name": "Mouse", "price": 29.99, "stock": 0},
        {"id": 3, "name": "Monitor", "price": 249.0, "stock": 5},
    ],
}


def describe_schema() -> dict[str, list[str]]:
    return {table: list(columns) for table, columns in SCHEMA.items()}
