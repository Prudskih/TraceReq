"""SQLAlchemy: модели и отдельная сессия на каждый HTTP-запрос."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import Config


class Base(DeclarativeBase):
    pass


database_url = make_url(Config.SQLALCHEMY_DATABASE_URI)
connect_args = {}
if database_url.get_backend_name() == 'sqlite':
    connect_args['check_same_thread'] = False
    # Относительные SQLite-пути сохраняют прежнее расположение в instance/.
    if database_url.database and database_url.database != ':memory:':
        path = Path(database_url.database)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / 'instance' / path
            database_url = database_url.set(database=str(path))

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """Закрываем сессию и откатываем незавершённую транзакцию после запроса."""
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
