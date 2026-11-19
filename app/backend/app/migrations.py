"""Additive schema migrations for existing databases.

`Base.metadata.create_all()` creates missing tables but never changes existing
ones. This module adds columns that newer code expects to tables that already
exist. Rules:

- Only `ALTER TABLE ... ADD COLUMN` for nullable columns without defaults:
  nothing is dropped, renamed, rewritten, or recreated, and existing rows keep
  NULL in the new column.
- Idempotent: a column that already exists is skipped, so it is safe to run on
  every startup and on fresh databases (where create_all already added it).
- Column types are compiled from the SQLAlchemy models for the connected
  database, so the same list works on SQLite (local) and Postgres (Render).

Older code ignores the extra columns, so a migrated database still works if
the application code is rolled back.
"""

import logging

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from . import models

logger = logging.getLogger(__name__)

# (model, column attribute) pairs added after their table first shipped.
ADDITIVE_COLUMNS = [
    (models.CareerChatMessage, "resources"),
    (models.CareerRoadmap, "portfolio_fingerprint"),
    (models.RoadmapProposal, "origin"),
    (models.RoadmapProposal, "portfolio_fingerprint"),
    (models.AIUsageEvent, "status"),
]


def pending_columns(engine: Engine) -> list[tuple[str, str]]:
    """(table, column) pairs that are in the models but not the database."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing = []

    for model, attribute in ADDITIVE_COLUMNS:
        table = model.__table__
        if table.name not in tables:
            continue  # create_all creates the whole table, columns included
        existing = {column["name"] for column in inspector.get_columns(table.name)}
        if table.c[attribute].name not in existing:
            missing.append((table.name, table.c[attribute].name))

    return missing


def run_additive_migrations(engine: Engine) -> list[tuple[str, str]]:
    """Add any missing columns in one transaction. Returns what was added."""
    missing = pending_columns(engine)
    if not missing:
        return []

    preparer = engine.dialect.identifier_preparer

    with engine.begin() as connection:
        for table_name, column_name in missing:
            column = models.Base.metadata.tables[table_name].c[column_name]
            if not column.nullable or column.server_default is not None:
                raise RuntimeError(f"{table_name}.{column_name} is not additive-safe")

            column_type = column.type.compile(dialect=engine.dialect)
            connection.exec_driver_sql(
                f"ALTER TABLE {preparer.quote(table_name)} "
                f"ADD COLUMN {preparer.quote(column_name)} {column_type}"
            )
            logger.info("Migration: added column %s.%s", table_name, column_name)

    return missing
