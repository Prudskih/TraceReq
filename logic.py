
"""Простая бизнес-логика"""

from datetime import datetime

from sqlalchemy.orm import Session
from models.requirement import Requirement
from models.link import Link
from models.history import RequirementHistory


def _save_history(session: Session, requirement_id, change_type, old_values, new_values, who):
    """Сохраняем событие в историю изменений."""
    h = RequirementHistory(
        requirement_id=requirement_id,
        change_type=change_type,
        old_values=old_values,
        new_values=new_values,
        changed_by=who,
        changed_at=datetime.utcnow(),
    )
    session.add(h)
    session.commit()


def get_requirement_with_links(session: Session, project_id,requirement_id):
    """Требование + входящие/исходящие связи."""
    req = session.get(Requirement, requirement_id)
    if not req or req.project_id != project_id:
        return None

    outgoing = (((session.query(Link)
                .join(Requirement, Link.target_requirement_id == Requirement.id))
                .filter(Link.source_requirement_id == requirement_id))
                .all())
    incoming = ((session.query(Link)
                .join(Requirement, Link.source_requirement_id == Requirement.id)
                .filter(Link.target_requirement_id == requirement_id))
                .all())

    d = req.to_dict()
    d['outgoing_links'] = [link.to_dict() for link in outgoing]
    d['incoming_links'] = [link.to_dict() for link in incoming]
    return d


def get_all_requirements_with_links(session: Session, project_id):
    """Все требования со связями"""
    reqs = (session.query(Requirement)
            .filter(Requirement.project_id == project_id)
            .order_by(Requirement.id.asc())
            .all())
    return [get_requirement_with_links(session, project_id, req.id) for req in reqs if req]


def create_requirement(session: Session, project_id: int, requirement_data: dict, author=None):
    """Создание требования."""
    requirement_data['project_id'] = project_id
    if author:
        requirement_data['author'] = author

    req = Requirement(**requirement_data)
    session.add(req)
    session.commit()

    _save_history(session, req.id, 'CREATE', None, req.to_dict(), author)
    return req


def update_requirement(session: Session, project_id:int,requirement_id:int, fields, changed_by=None):
    """Обновление требования."""
    req = session.get(Requirement, requirement_id)
    if not req or req.project_id != project_id:
        return None

    old_values = req.to_dict()

    for k, v in fields.items():
        setattr(req, k, v)

    session.commit()
    _save_history(session, requirement_id, 'UPDATE', old_values, req.to_dict(), changed_by)
    return req


def delete_requirement(session: Session, project_id:int,requirement_id:int, deleted_by=None):
    """Удаление требования."""
    req = session.get(Requirement, requirement_id)
    if not req or req.project_id != project_id:
        return False

    old_values = req.to_dict()

    session.query(Link).filter(
        (Link.source_requirement_id == requirement_id)
        | (Link.target_requirement_id == requirement_id)
    ).delete(synchronize_session=False)

    session.delete(req)
    session.commit()

    _save_history(session, requirement_id, 'DELETE', old_values, None, deleted_by)
    return True


def create_link(session: Session, project_id:int, source_id:int, target_id:int, link_type):
    """Создание связи между требованиями."""
    if source_id == target_id:
        return None

    src = session.get(Requirement, source_id)
    tgt = session.get(Requirement, target_id)
    if not src or not tgt:
        return None
    if src.project_id != project_id or tgt.project_id != project_id:
        return None

    link = Link(
        source_requirement_id=source_id,
        target_requirement_id=target_id,
        link_type=link_type,
    )
    session.add(link)
    session.commit()
    return link


def delete_link(session: Session, link_id):
    """Удаление связи."""
    link = session.get(Link, link_id)
    if not link:
        return False

    session.delete(link)
    session.commit()
    return True


def get_history(session: Session, requirement_id):
    """История изменений требования."""
    return (
        session.query(RequirementHistory)
        .filter(RequirementHistory.requirement_id == requirement_id)
        .order_by(RequirementHistory.changed_at.desc())
        .all()
    )


def build_matrix(session: Session, project_id: int):
    """Матрица пересечений: source -> target -> тип связи."""
    reqs = (session.query(Requirement)
            .filter(Requirement.project_id == project_id)
            .order_by(Requirement.id.asc())
            .all())

    req_ids = [req.id for req in reqs]

    links = (session.query(Link)
             .filter(Link.source_requirement_id.in_(req_ids))
             .filter(Link.target_requirement_id.in_(req_ids))
             .all())

    matrix = {}
    for l in links:
        matrix.setdefault(l.source_requirement_id, {})[l.target_requirement_id] = l.link_type.value

    return reqs, matrix, links
