
"""Простая бизнес-логика"""

from datetime import datetime

from database import db
from models.requirement import Requirement
from models.link import Link
from models.history import RequirementHistory


def _save_history(requirement_id, change_type, old_values, new_values, who):
    """Сохраняем событие в историю изменений."""
    h = RequirementHistory(
        requirement_id=requirement_id,
        change_type=change_type,
        old_values=old_values,
        new_values=new_values,
        changed_by=who,
        changed_at=datetime.utcnow(),
    )
    db.session.add(h)
    db.session.commit()


def get_requirement_with_links(project_id,requirement_id):
    """Требование + входящие/исходящие связи."""
    req = db.session.get(Requirement, requirement_id)
    if not req or req.project_id != project_id:
        return None

    outgoing = (((db.session.query(Link)
                .join(Requirement, Link.target_requirement_id == Requirement.id))
                .filter(Link.source_requirement_id == requirement_id))
                .all())
    incoming = ((db.session.query(Link)
                .join(Requirement, Link.source_requirement_id == Requirement.id)
                .filter(Link.target_requirement_id == requirement_id))
                .all())

    d = req.to_dict()
    d['outgoing_links'] = [link.to_dict() for link in outgoing]
    d['incoming_links'] = [link.to_dict() for link in incoming]
    return d


def get_all_requirements_with_links(project_id):
    """Все требования со связями"""
    reqs = (db.session.query(Requirement)
            .filter(Requirement.project_id == project_id)
            .order_by(Requirement.id.asc())
            .all())
    return [get_requirement_with_links(project_id, req.id) for req in reqs if req]


def create_requirement(project_id: int, requirement_data: dict, author=None):
    """Создание требования."""
    requirement_data['project_id'] = project_id
    if author:
        requirement_data['author'] = author

    req = Requirement(**requirement_data)
    db.session.add(req)
    db.session.commit()

    _save_history(req.id, 'CREATE', None, req.to_dict(), author)
    return req


def update_requirement(project_id:int,requirement_id:int, fields, changed_by=None):
    """Обновление требования."""
    req = db.session.get(Requirement, requirement_id)
    if not req or req.project_id != project_id:
        return None

    old_values = req.to_dict()

    for k, v in fields.items():
        setattr(req, k, v)

    db.session.commit()
    _save_history(requirement_id, 'UPDATE', old_values, req.to_dict(), changed_by)
    return req


def delete_requirement(project_id:int,requirement_id:int, deleted_by=None):
    """Удаление требования."""
    req = db.session.get(Requirement, requirement_id)
    if not req or req.project_id != project_id:
        return False

    old_values = req.to_dict()

    db.session.query(Link).filter(
        (Link.source_requirement_id == requirement_id)
        | (Link.target_requirement_id == requirement_id)
    ).delete(synchronize_session=False)

    db.session.delete(req)
    db.session.commit()

    _save_history(requirement_id, 'DELETE', old_values, None, deleted_by)
    return True


def create_link(project_id:int, source_id:int, target_id:int, link_type):
    """Создание связи между требованиями."""
    if source_id == target_id:
        return None

    src = db.session.get(Requirement, source_id)
    tgt = db.session.get(Requirement, target_id)
    if not src or not tgt:
        return None
    if src.project_id != project_id or tgt.project_id != project_id:
        return None

    link = Link(
        source_requirement_id=source_id,
        target_requirement_id=target_id,
        link_type=link_type,
    )
    db.session.add(link)
    db.session.commit()
    return link


def delete_link(link_id):
    """Удаление связи."""
    link = db.session.get(Link, link_id)
    if not link:
        return False

    db.session.delete(link)
    db.session.commit()
    return True


def get_history(requirement_id):
    """История изменений требования."""
    return (
        db.session.query(RequirementHistory)
        .filter(RequirementHistory.requirement_id == requirement_id)
        .order_by(RequirementHistory.changed_at.desc())
        .all()
    )


def build_matrix(project_id: int):
    """Матрица пересечений: source -> target -> тип связи."""
    reqs = (db.session.query(Requirement)
            .filter(Requirement.project_id == project_id)
            .order_by(Requirement.id.asc())
            .all())

    req_ids = [req.id for req in reqs]

    links = (db.session.query(Link)
             .filter(Link.source_requirement_id.in_(req_ids))
             .filter(Link.target_requirement_id.in_(req_ids))
             .all())

    matrix = {}
    for l in links:
        matrix.setdefault(l.source_requirement_id, {})[l.target_requirement_id] = l.link_type.value

    return reqs, matrix, links
