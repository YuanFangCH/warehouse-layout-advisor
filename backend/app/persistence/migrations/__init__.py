"""SQLite schema migrations for the first version.

The initial schema is created idempotently by database.init_db() using the
SQLAlchemy metadata in app.models.entities. Keeping this package here gives
later multi-user deployments a place to add numbered upgrade scripts.
"""
