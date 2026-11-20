"""The additive startup migration on a database created before P1."""

import json

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session

from app import models
from app.migrations import pending_columns, run_additive_migrations

# The pre-P1 shape of the three tables that gain columns.
OLD_SCHEMA = [
    """CREATE TABLE career_chat_messages (
        id INTEGER PRIMARY KEY, portfolio_id INTEGER NOT NULL,
        role VARCHAR(20) NOT NULL, content TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE career_roadmaps (
        id INTEGER PRIMARY KEY, portfolio_id INTEGER NOT NULL UNIQUE,
        title VARCHAR(200) NOT NULL, goals JSON NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE roadmap_proposals (
        id INTEGER PRIMARY KEY, portfolio_id INTEGER NOT NULL,
        title VARCHAR(200) NOT NULL, goals JSON NOT NULL,
        status VARCHAR(20) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""",
]

GOALS = [{"id": "g", "title": "Goal", "milestones": [{"id": "m", "title": "Done", "completed": True}]}]


def _old_database(path):
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as db:
        for statement in OLD_SCHEMA:
            db.exec_driver_sql(statement)
        db.execute(text("INSERT INTO career_chat_messages (portfolio_id, role, content) "
                        "VALUES (1, 'user', 'hi'), (1, 'assistant', 'hello')"))
        db.execute(text("INSERT INTO career_roadmaps (portfolio_id, title, goals) VALUES (1, 'Mine', :g)"),
                   {"g": json.dumps(GOALS)})
        db.execute(text("INSERT INTO roadmap_proposals (portfolio_id, title, goals, status) "
                        "VALUES (1, 'Draft', :g, 'pending')"), {"g": json.dumps(GOALS)})
    return engine


def _rows(engine):
    with engine.connect() as db:
        return {
            table: db.execute(text(f"SELECT * FROM {table} ORDER BY id")).mappings().all()
            for table in ("career_chat_messages", "career_roadmaps", "roadmap_proposals")
        }


def test_migration_adds_nullable_columns_and_keeps_every_row(tmp_path):
    engine = _old_database(tmp_path / "old.db")
    before = _rows(engine)

    added = run_additive_migrations(engine)
    assert sorted(added) == [
        ("career_chat_messages", "resources"),
        ("career_roadmaps", "portfolio_fingerprint"),
        ("roadmap_proposals", "origin"),
        ("roadmap_proposals", "portfolio_fingerprint"),
    ]

    after = _rows(engine)
    for table, rows in before.items():
        assert len(after[table]) == len(rows)
        for old, new in zip(rows, after[table]):
            assert {k: new[k] for k in old.keys()} == dict(old)  # existing values unchanged
            assert all(new[k] is None for k in set(new.keys()) - set(old.keys()))

    # Repeatable: a second run changes nothing.
    assert run_additive_migrations(engine) == []
    assert pending_columns(engine) == []
    assert _rows(engine) == after

    # The models read the migrated rows, progress included.
    with Session(engine) as db:
        roadmap = db.scalar(select(models.CareerRoadmap))
        assert roadmap.goals == GOALS and roadmap.portfolio_fingerprint is None
        assert db.scalar(select(models.RoadmapProposal)).origin is None
    engine.dispose()


def test_fresh_database_needs_no_migration(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'new.db'}")
    models.Base.metadata.create_all(engine)
    assert "ai_usage_events" in inspect(engine).get_table_names()
    assert run_additive_migrations(engine) == []
    engine.dispose()


def test_usage_table_from_first_p1_build_gains_status(tmp_path):
    """Databases migrated by the first P1 build have ai_usage_events without
    `status`; the column is added and logged rows are kept."""
    engine = create_engine(f"sqlite:///{tmp_path / 'p1.db'}")
    with engine.begin() as db:
        db.exec_driver_sql(
            """CREATE TABLE ai_usage_events (
                id INTEGER PRIMARY KEY, portfolio_id INTEGER NOT NULL,
                kind VARCHAR(20) NOT NULL, provider VARCHAR(20) NOT NULL,
                web_searches INTEGER NOT NULL, input_tokens INTEGER,
                output_tokens INTEGER, created_at DATETIME)"""
        )
        db.exec_driver_sql(
            "INSERT INTO ai_usage_events (portfolio_id, kind, provider, web_searches, input_tokens)"
            " VALUES (1, 'chat', 'openai', 0, 50)"
        )

    assert run_additive_migrations(engine) == [("ai_usage_events", "status")]
    assert run_additive_migrations(engine) == []
    with engine.connect() as db:
        row = db.execute(text("SELECT kind, input_tokens, status FROM ai_usage_events")).one()
    assert tuple(row) == ("chat", 50, None)
    engine.dispose()
