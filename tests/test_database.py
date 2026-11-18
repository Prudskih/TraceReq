from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from tracereq.infrastructure.persistence.database import create_database_engine
from tracereq.settings import Settings
from tracereq.web.app import create_app


def test_app_startup_does_not_create_or_migrate_database(tmp_path):
    path = tmp_path / 'existing.sqlite'
    settings = Settings(_env_file=None, database_url=f'sqlite:///{path.as_posix()}')
    engine = create_database_engine(settings)
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE sentinel (value TEXT NOT NULL)'))
        connection.execute(text("INSERT INTO sentinel VALUES ('unchanged')"))
    engine.dispose()
    before = path.read_bytes()
    with TestClient(create_app(settings)) as client:
        assert client.get('/').status_code == 200
        assert client.get('/openapi.json').status_code == 200
    assert path.read_bytes() == before


def test_relative_sqlite_path_and_foreign_keys(tmp_path):
    engine = create_database_engine(
        Settings(
            _env_file=None,
            database_url='sqlite:///test.sqlite',
            instance_dir=tmp_path,
        )
    )
    try:
        assert Path(engine.url.database) == tmp_path / 'test.sqlite'
        with engine.connect() as connection:
            assert connection.scalar(text('PRAGMA foreign_keys')) == 1
        assert inspect(engine).get_table_names() == []
    finally:
        engine.dispose()


def test_legacy_schema_is_usable_without_migration(tmp_path):
    settings = Settings(
        _env_file=None, database_url=f'sqlite:///{(tmp_path / "legacy.db").as_posix()}'
    )
    engine = create_database_engine(settings)
    # SQL mirrors the previous on-disk layout, independent of the new ORM metadata.
    statements = [
        'CREATE TABLE projects (id INTEGER PRIMARY KEY, name VARCHAR(200) NOT NULL UNIQUE, '
        'description VARCHAR(1000) NOT NULL, created_at DATETIME)',
        'CREATE TABLE requirements (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id), '
        'title VARCHAR(500) NOT NULL, description TEXT, requirement_type VARCHAR(14) NOT NULL, '
        'status VARCHAR(11), priority VARCHAR(8), source VARCHAR(500), author VARCHAR(200), '
        'created_at DATETIME, updated_at DATETIME)',
        'CREATE TABLE links (id INTEGER PRIMARY KEY, source_requirement_id INTEGER NOT NULL REFERENCES requirements(id), '
        'target_requirement_id INTEGER NOT NULL REFERENCES requirements(id), link_type VARCHAR(11) NOT NULL)',
        'CREATE TABLE requirement_history (id INTEGER PRIMARY KEY, requirement_id INTEGER NOT NULL REFERENCES requirements(id), '
        'changed_by VARCHAR(200), changed_at DATETIME, change_type VARCHAR(50), old_values JSON, new_values JSON)',
        "INSERT INTO projects VALUES (1, 'Legacy', '', '2024-01-01 12:00:00')",
        "INSERT INTO requirements VALUES (1, 1, 'Old requirement', '', 'BUSINESS', 'DRAFT', 'MEDIUM', '', '', "
        "'2024-01-01 12:00:00', '2024-01-01 12:00:00')",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    engine.dispose()
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/projects').json()[0]['name'] == 'Legacy'
        assert (
            client.get('/api/projects/1/requirements/1').json()['requirement_type']
            == 'Бизнес-требование'
        )
        assert (
            client.put('/api/projects/1/requirements/1', json={'title': 'Updated'}).status_code
            == 200
        )
        assert len(client.get('/api/projects/1/requirements/1/history').json()) == 1
        assert client.delete('/api/projects/1').status_code == 200
