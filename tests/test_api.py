import pytest
from sqlalchemy import func, select

from tracereq.infrastructure.persistence.models import (
    HistoryRow,
    LinkRow,
    ProjectRow,
    RequirementRow,
)


def test_pages_static_and_openapi(client, project):
    assert client.get('/').status_code == 200
    page = client.get(f'/project/{project["id"]}')
    assert page.status_code == 200
    assert project['name'] in page.text
    for asset in ('css/style.css', 'js/main.js', 'js/projects.js'):
        assert client.get(f'/static/{asset}').status_code == 200
    assert client.get('/docs').status_code == 200
    schema = client.get('/openapi.json').json()
    assert '/api/projects/{project_id}/requirements/import/docx' in schema['paths']
    assert schema['paths']['/api/projects']['post']['responses']['201']


def test_project_crud_and_unique_name_conflict(client):
    created = client.post('/api/projects', json={'name': '  Alpha  ', 'description': ' Original '})
    assert created.status_code == 201
    project = created.json()
    assert project['name'] == 'Alpha'
    assert project['description'] == 'Original'
    assert project['created_at'].endswith('GMT')
    duplicate = client.post('/api/projects', json={'name': 'Alpha'})
    assert duplicate.status_code == 409
    assert set(duplicate.json()) == {'error'}
    assert 'INSERT' not in duplicate.text
    assert len(client.get('/api/projects').json()) == 1
    url = f'/api/projects/{project["id"]}'
    assert client.put(url, json={'description': 'Changed'}).json()['name'] == 'Alpha'
    assert client.put(url, json={}).json()['description'] == 'Changed'
    assert client.delete(url).status_code == 200
    assert client.get('/api/projects').json() == []
    assert client.delete(url).status_code == 404


@pytest.mark.parametrize(
    'payload',
    [
        {},
        {'name': ' '},
        {'name': 'x' * 201},
        {'name': None},
        {'name': 'Valid', 'unknown': True},
        {'name': 'Valid', 'description': 'x' * 1001},
    ],
)
def test_project_validation(client, payload):
    response = client.post('/api/projects', json=payload)
    assert response.status_code == 422
    assert set(response.json()) == {'error'}
    assert client.get('/api/projects').json() == []


def test_requirement_update_history_and_delete(client, project, requirement_factory, app):
    requirement = requirement_factory(author='Автор')
    base = f'/api/projects/{project["id"]}/requirements'
    url = f'{base}/{requirement["id"]}'
    assert requirement['status'] == 'Черновик'
    assert requirement['priority'] == 'Средний'
    assert client.get(url).json()['outgoing_links'] == []
    response = client.put(url, json={'title': 'Новое название', 'changed_by': 'Редактор'})
    assert response.status_code == 200
    assert response.json()['author'] == 'Автор'
    history = client.get(f'{url}/history').json()
    assert [entry['change_type'] for entry in history] == ['UPDATE', 'CREATE']
    assert history[0]['changed_by'] == 'Редактор'
    assert history[0]['old_values']['title'] == 'Требование'
    assert history[0]['new_values']['title'] == 'Новое название'
    assert client.request('DELETE', url, json={'deleted_by': 'Редактор'}).status_code == 200
    assert client.get(url).status_code == 404
    assert client.get(f'{url}/history').status_code == 404
    with app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(HistoryRow)) == 0


@pytest.mark.parametrize(
    'fields',
    [
        {'title': ''},
        {'title': None},
        {'title': 'x' * 501},
        {'requirement_type': 'invalid'},
        {'status': 'invalid'},
        {'priority': None},
        {'source': 'x' * 501},
        {'author': 'x' * 201},
        {'project_id': 123},
    ],
)
def test_requirement_validation_preserves_state(client, project, requirement_factory, fields):
    requirement = requirement_factory()
    url = f'/api/projects/{project["id"]}/requirements/{requirement["id"]}'
    response = client.put(url, json=fields)
    assert response.status_code == 422
    assert client.get(url).json()['title'] == requirement['title']
    assert len(client.get(f'{url}/history').json()) == 1


def test_links_matrix_and_project_isolation(client, project, requirement_factory):
    first = requirement_factory(title='First')
    second = requirement_factory(title='Second')
    base = f'/api/projects/{project["id"]}'
    link = client.post(
        f'{base}/links',
        json={
            'source_id': first['id'],
            'target_id': second['id'],
            'link_type': 'Зависит от',
        },
    )
    assert link.status_code == 201
    requirements = client.get(f'{base}/requirements').json()
    assert requirements[0]['outgoing_links'] == [link.json()]
    assert requirements[1]['incoming_links'] == [link.json()]
    matrix = client.get(f'{base}/matrix').json()['matrix']
    assert matrix == {str(first['id']): {str(second['id']): 'Зависит от'}}
    other = client.post('/api/projects', json={'name': 'Other'}).json()['id']
    other_url = f'/api/projects/{other}/requirements/{first["id"]}'
    for method in ('get', 'put', 'delete'):
        response = client.request(
            method, other_url, **({'json': {'title': 'Hacked'}} if method == 'put' else {})
        )
        assert response.status_code == 404
    assert client.get(f'{other_url}/history').status_code == 404
    assert (
        client.post(
            f'/api/projects/{other}/links',
            json={
                'source_id': first['id'],
                'target_id': second['id'],
                'link_type': 'Реализует',
            },
        ).status_code
        == 400
    )
    assert (
        client.post(
            f'{base}/links',
            json={
                'source_id': first['id'],
                'target_id': first['id'],
                'link_type': 'Реализует',
            },
        ).status_code
        == 400
    )
    assert client.delete(f'/api/links/{link.json()["id"]}').status_code == 200
    assert client.get(f'{base}/matrix').json()['matrix'] == {}


@pytest.mark.parametrize('target', ['requirement', 'project'])
def test_deletion_cleans_dependent_rows(client, project, requirement_factory, app, target):
    first, second = requirement_factory(), requirement_factory()
    base = f'/api/projects/{project["id"]}'
    assert (
        client.post(
            f'{base}/links',
            json={
                'source_id': first['id'],
                'target_id': second['id'],
                'link_type': 'Реализует',
            },
        ).status_code
        == 201
    )
    url = base if target == 'project' else f'{base}/requirements/{first["id"]}'
    assert client.delete(url).status_code == 200
    with app.state.session_factory() as session:
        counts = {
            model.__name__: session.scalar(select(func.count()).select_from(model))
            for model in (ProjectRow, RequirementRow, LinkRow, HistoryRow)
        }
    assert counts == (
        {'ProjectRow': 0, 'RequirementRow': 0, 'LinkRow': 0, 'HistoryRow': 0}
        if target == 'project'
        else {'ProjectRow': 1, 'RequirementRow': 1, 'LinkRow': 0, 'HistoryRow': 1}
    )


@pytest.mark.parametrize(
    'path',
    [
        '/project/999',
        '/api/projects/999/requirements',
        '/api/projects/999/matrix',
        '/api/projects/999/export',
        '/api/projects/999/export/matrix',
        '/api/projects/999/requirements/999',
        '/api/projects/999/requirements/999/history',
    ],
)
def test_missing_resources(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert set(response.json()) == {'error'}


def test_cannot_create_requirement_without_project(client):
    response = client.post(
        '/api/projects/999/requirements',
        json={
            'title': 'Orphan',
            'requirement_type': 'Бизнес-требование',
        },
    )
    assert response.status_code == 404
