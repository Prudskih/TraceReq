
"""Простая бизнес-логика (учебный проект)."""

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


def get_requirement_with_links(requirement_id):
    """Требование + входящие/исходящие связи."""
    req = db.session.get(Requirement, requirement_id)
    if not req:
        return None

    outgoing = db.session.query(Link).filter_by(source_requirement_id=requirement_id).all()
    incoming = db.session.query(Link).filter_by(target_requirement_id=requirement_id).all()

    d = req.to_dict()
    d['outgoing_links'] = [l.to_dict() for l in outgoing]
    d['incoming_links'] = [l.to_dict() for l in incoming]
    return d


def get_all_requirements_with_links():
    """Все требования со связями"""
    reqs = db.session.query(Requirement).order_by(Requirement.id.asc()).all()
    result = []
    for r in reqs:
        d = get_requirement_with_links(r.id)
        if d:
            result.append(d)
    return result


def create_requirement(requirement_data, author=None):
    """Создание требования."""
    if author:
        requirement_data['author'] = author

    req = Requirement(**requirement_data)
    db.session.add(req)
    db.session.commit()

    _save_history(req.id, 'CREATE', None, req.to_dict(), author)
    return req


def update_requirement(requirement_id, fields, changed_by=None):
    """Обновление требования."""
    req = db.session.get(Requirement, requirement_id)
    if not req:
        return None

    old_values = req.to_dict()

    for k, v in fields.items():
        setattr(req, k, v)

    db.session.commit()
    _save_history(requirement_id, 'UPDATE', old_values, req.to_dict(), changed_by)
    return req


def delete_requirement(requirement_id, deleted_by=None):
    """Удаление требования."""
    req = db.session.get(Requirement, requirement_id)
    if not req:
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


def create_link(source_id, target_id, link_type):
    """Создание связи между требованиями."""
    if source_id == target_id:
        return None

    src = db.session.get(Requirement, source_id)
    tgt = db.session.get(Requirement, target_id)
    if not src or not tgt:
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


def build_matrix():
    """Матрица пересечений: source -> target -> тип связи."""
    reqs = db.session.query(Requirement).order_by(Requirement.id.asc()).all()
    links = db.session.query(Link).all()

    matrix = {}
    for l in links:
        matrix.setdefault(l.source_requirement_id, {})[l.target_requirement_id] = l.link_type.value

    return reqs, matrix, links
