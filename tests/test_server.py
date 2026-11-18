"""Smoke test of the installed entry point over a real TCP connection."""

import os
import socket
import subprocess
import sys
import time

import httpx

from tracereq.infrastructure.persistence.database import create_database_engine
from tracereq.infrastructure.persistence.models import Base
from tracereq.settings import Settings


def test_cli_server_serves_http(tmp_path):
    database_url = f'sqlite:///{(tmp_path / "server.sqlite").as_posix()}'
    engine = create_database_engine(Settings(_env_file=None, database_url=database_url))
    Base.metadata.create_all(engine)
    engine.dispose()
    with socket.socket() as port_socket:
        port_socket.bind(('127.0.0.1', 0))
        port = port_socket.getsockname()[1]
    environment = os.environ | {
        'DATABASE_URL': database_url,
        'HOST': '127.0.0.1',
        'PORT': str(port),
        'PYTHONIOENCODING': 'utf-8',
    }
    log_path = tmp_path / 'server.log'
    with log_path.open('w', encoding='utf-8') as log:
        process = subprocess.Popen(
            [sys.executable, '-m', 'tracereq'],
            cwd=tmp_path,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        try:
            with httpx.Client(
                base_url=f'http://127.0.0.1:{port}', timeout=1, trust_env=False
            ) as client:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise AssertionError(log_path.read_text(encoding='utf-8'))
                    try:
                        response = client.get('/')
                        break
                    except httpx.TransportError:
                        time.sleep(0.1)
                else:
                    raise AssertionError(
                        'Server did not become ready: ' + log_path.read_text(encoding='utf-8')
                    )
                assert response.status_code == 200
                assert client.get('/static/js/main.js').status_code == 200
                created = client.post('/api/projects', json={'name': 'Live server'})
                assert created.status_code == 201
                assert client.get('/api/projects').json()[0]['id'] == created.json()['id']
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
