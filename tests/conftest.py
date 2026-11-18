from io import BytesIO

import pytest
from docx import Document
from fastapi.testclient import TestClient

from tracereq.infrastructure.persistence.models import Base
from tracereq.settings import Settings
from tracereq.web.app import create_app


@pytest.fixture
def app():
    return create_app(
        Settings(_env_file=None, database_url='sqlite:///:memory:', max_upload_bytes=100_000)
    )


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        # Only the explicitly configured, per-test in-memory database is initialized.
        Base.metadata.create_all(app.state.session_factory.kw['bind'])
        yield client


@pytest.fixture
def project(client):
    response = client.post('/api/projects', json={'name': 'Проект', 'description': 'Описание'})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def requirement_factory(client, project):
    def create(**overrides):
        payload = {'title': 'Требование', 'requirement_type': 'Бизнес-требование'} | overrides
        response = client.post(f'/api/projects/{project["id"]}/requirements', json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return create


@pytest.fixture
def docx_bytes():
    def build(*paragraphs):
        document = Document()
        for text in paragraphs:
            document.add_paragraph(text)
        output = BytesIO()
        document.save(output)
        return output.getvalue()

    return build
