from io import BytesIO

import pytest
from openpyxl import load_workbook


def test_docx_import_sections_end_markers_and_history(client, project, docx_bytes):
    content = docx_bytes(
        '<Бизнес-требования>',
        '- Первое требование',
        '- Второе требование',
        '<конец>',
        '- Не импортировать',
        '<Функциональные требования>',
        '- Третье требование',
        '<end>',
        '- Тоже не импортировать',
    )
    base = f'/api/projects/{project["id"]}/requirements'
    response = client.post(f'{base}/import/docx', files={'file': ('requirements.docx', content)})
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload['created_count'] == 3
    assert [item['requirement_type'] for item in payload['requirements']] == [
        'Бизнес-требование',
        'Бизнес-требование',
        'Функциональное требование',
    ]
    assert payload['requirements'][1]['title'] == 'Бизнес-требование 2'
    assert len(client.get(base).json()) == 3
    for requirement in payload['requirements']:
        history = client.get(f'{base}/{requirement["id"]}/history').json()
        assert len(history) == 1
        assert history[0]['new_values']['description'] == requirement['description']


@pytest.mark.parametrize(
    'filename,content',
    [
        ('requirements.txt', b'plain text'),
        ('empty.docx', b''),
        ('invalid.docx', b'not a zip'),
    ],
)
def test_invalid_upload_does_not_write(client, project, filename, content):
    base = f'/api/projects/{project["id"]}/requirements'
    response = client.post(f'{base}/import/docx', files={'file': (filename, content)})
    assert response.status_code == 400
    assert set(response.json()) == {'error'}
    assert client.get(base).json() == []


def test_missing_and_oversized_upload(client, project):
    url = f'/api/projects/{project["id"]}/requirements/import/docx'
    assert client.post(url).status_code == 400
    response = client.post(url, files={'file': ('large.docx', b'x' * 100_001)})
    assert response.status_code == 400
    assert 'размер' in response.json()['error']


def test_docx_without_requirements(client, project, docx_bytes):
    response = client.post(
        f'/api/projects/{project["id"]}/requirements/import/docx',
        files={'file': ('empty.docx', docx_bytes('Обычный текст'))},
    )
    assert response.status_code == 400
    assert 'Не найдено требований' in response.json()['error']


def test_xlsx_exports_content_and_formula_safety(client, project, requirement_factory):
    first = requirement_factory(title='=1+1', author='=SUM(A1:A2)')
    second = requirement_factory(title='Обычное требование')
    base = f'/api/projects/{project["id"]}'
    assert (
        client.post(
            f'{base}/links',
            json={
                'source_id': first['id'],
                'target_id': second['id'],
                'link_type': 'Противоречит',
            },
        ).status_code
        == 201
    )
    response = client.get(f'{base}/export')
    assert response.status_code == 200
    assert response.headers['content-type'].endswith('spreadsheetml.sheet')
    assert 'requirements_trace.xlsx' in response.headers['content-disposition']
    workbook = load_workbook(BytesIO(response.content))
    try:
        assert workbook.sheetnames == ['Requirements', 'Links']
        assert workbook['Requirements']['B2'].value == '=1+1'
        assert workbook['Requirements']['B2'].data_type == 's'
        assert workbook['Requirements']['G2'].data_type == 's'
        assert list(workbook['Links'].values)[1][1:] == (first['id'], second['id'], 'Противоречит')
    finally:
        workbook.close()
    matrix_response = client.get(f'{base}/export/matrix')
    assert matrix_response.status_code == 200
    workbook = load_workbook(BytesIO(matrix_response.content))
    try:
        assert list(workbook['Matrix'].values) == [
            (None, f'#{first["id"]}', f'#{second["id"]}'),
            (f'#{first["id"]}', '-', 'Противоречит'),
            (f'#{second["id"]}', None, '-'),
        ]
    finally:
        workbook.close()


def test_empty_project_exports(client, project):
    base = f'/api/projects/{project["id"]}'
    assert client.get(f'{base}/matrix').json() == {'requirements': [], 'matrix': {}}
    for suffix in ('/export', '/export/matrix'):
        response = client.get(base + suffix)
        assert response.status_code == 200
        workbook = load_workbook(BytesIO(response.content))
        workbook.close()
