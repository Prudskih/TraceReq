"""Создание engine не открывает соединение и не меняет схему БД."""

from pathlib import Path
from sqlite3 import Connection

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.pool import ConnectionPoolEntry, StaticPool

from tracereq.settings import Settings


def create_database_engine(settings: Settings) -> Engine:
    url = make_url(settings.database_url)
    if url.get_backend_name() != 'sqlite':
        return create_engine(url, pool_pre_ping=True)

    if not url.database or url.database == ':memory:':
        engine = create_engine(url, connect_args={'check_same_thread': False}, poolclass=StaticPool)
    else:
        path = Path(url.database)
        if not path.is_absolute():
            url = url.set(database=str((settings.instance_dir / path).resolve()))
        engine = create_engine(url, connect_args={'check_same_thread': False})

    @event.listens_for(engine, 'connect')
    def enable_foreign_keys(connection: Connection, _record: ConnectionPoolEntry) -> None:
        cursor = connection.cursor()
        try:
            cursor.execute('PRAGMA foreign_keys=ON')
        finally:
            cursor.close()

    return engine
