import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from tracereq.infrastructure.persistence.initialization import initialize_database
from tracereq.settings import Settings
from tracereq.web.app import create_app


def test_initialize_new_database_supports_first_project(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url='sqlite:///requirements_trace.db',
        instance_dir=tmp_path / 'instance',
    )
    path = initialize_database(settings)
    assert path == tmp_path / 'instance' / 'requirements_trace.db'
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/projects').json() == []
        response = client.post('/api/projects', json={'name': 'First project'})
        assert response.status_code == 201
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        initialize_database(settings)
    assert path.read_bytes() == before


@pytest.mark.parametrize('content', [b'', b'existing database must not change'])
def test_initialize_refuses_any_existing_file(tmp_path, content):
    path = tmp_path / 'existing.db'
    path.write_bytes(content)
    with pytest.raises(FileExistsError):
        initialize_database(Settings(_env_file=None, database_url=f'sqlite:///{path.as_posix()}'))
    assert path.read_bytes() == content


@pytest.mark.parametrize('url', ['sqlite:///:memory:', 'postgresql://localhost/example'])
def test_initialize_refuses_unsupported_targets(url):
    with pytest.raises(ValueError, match='new SQLite file'):
        initialize_database(Settings(_env_file=None, database_url=url))


def test_init_command_works_from_another_directory(tmp_path):
    environment = os.environ | {
        'DATABASE_URL': 'sqlite:///new.db',
        'INSTANCE_DIR': str(tmp_path / 'data'),
        'PYTHONIOENCODING': 'utf-8',
    }
    command = [sys.executable, '-m', 'tracereq', 'init-db']
    result = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr.decode('utf-8')
    assert (tmp_path / 'data' / 'new.db').is_file()
    result = subprocess.run(command, cwd=tmp_path, env=environment, capture_output=True, timeout=15)
    assert result.returncode == 1
    assert b'initialization refused' in result.stderr
