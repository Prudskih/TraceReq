"""Явная подготовка новой SQLite-базы; существующие файлы не изменяются."""

from pathlib import Path

from sqlalchemy.engine import make_url

from tracereq.infrastructure.persistence.database import create_database_engine
from tracereq.infrastructure.persistence.models import Base
from tracereq.settings import Settings


def initialize_database(settings: Settings) -> Path:
    url = make_url(settings.database_url)
    if (
        url.get_backend_name() != 'sqlite'
        or not url.database
        or url.database == ':memory:'
        or url.query
    ):
        raise ValueError('init-db supports only a new SQLite file without URL query parameters')
    engine = create_database_engine(settings)
    try:
        path = Path(str(engine.url.database))
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation refuses even an existing empty file. No migrations.
        with path.open('xb'):
            pass
        Base.metadata.create_all(engine)
        return path
    finally:
        engine.dispose()
