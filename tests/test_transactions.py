import pytest
from sqlalchemy import func, select

from tracereq.infrastructure.persistence.history import SqlAlchemyHistoryRepository
from tracereq.infrastructure.persistence.models import HistoryRow, RequirementRow
from tracereq.infrastructure.persistence.requirements import SqlAlchemyRequirementRepository


def test_failed_import_rolls_back_all_rows(client, app, project, docx_bytes, monkeypatch):
    original = SqlAlchemyRequirementRepository.add
    calls = 0

    def fail_second(self, project_id, fields):
        nonlocal calls
        result = original(self, project_id, fields)
        calls += 1
        if calls == 2:
            raise RuntimeError('simulated write failure')
        return result

    content = docx_bytes('<Бизнес-требования>', '- Один', '- Два')
    base = f'/api/projects/{project["id"]}/requirements'
    with monkeypatch.context() as patch:
        patch.setattr(SqlAlchemyRequirementRepository, 'add', fail_second)
        with pytest.raises(RuntimeError, match='simulated write failure'):
            client.post(f'{base}/import/docx', files={'file': ('import.docx', content)})
    with app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(RequirementRow)) == 0
        assert session.scalar(select(func.count()).select_from(HistoryRow)) == 0
    # The failed request must not poison later sessions.
    assert (
        client.post(f'{base}/import/docx', files={'file': ('import.docx', content)}).status_code
        == 201
    )


@pytest.mark.parametrize('operation', ['create', 'update'])
def test_history_failure_rolls_back_requirement(
    client, project, requirement_factory, monkeypatch, operation
):
    existing = requirement_factory(title='Original')
    base = f'/api/projects/{project["id"]}/requirements'
    url = f'{base}/{existing["id"]}'

    def fail_history(*args, **kwargs):
        raise RuntimeError('history unavailable')

    with monkeypatch.context() as patch:
        patch.setattr(SqlAlchemyHistoryRepository, 'add', fail_history)
        with pytest.raises(RuntimeError, match='history unavailable'):
            if operation == 'create':
                client.post(base, json={'title': 'New', 'requirement_type': 'Бизнес-требование'})
            else:
                client.put(url, json={'title': 'Changed'})
    requirements = client.get(base).json()
    assert len(requirements) == 1
    assert requirements[0]['title'] == 'Original'
    assert len(client.get(f'{url}/history').json()) == 1
