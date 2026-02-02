"""API маршруты"""

import tempfile

from flask import Blueprint, request, jsonify, send_file

from database import db
from models.project import Project
from models.requirement import Requirement, RequirementType, RequirementStatus, Priority
from models.link import Link, LinkType
from services.export_service import ExportService

import logic


api = Blueprint('api', __name__)


@api.route('/projects', methods=['POST'])
def create_project():
    data = request.get_json() or {}
    name = (data.get('name') or "").strip()
    description = (data.get('description') or "").strip()

    if not name:
        return jsonify({'error': 'name required'}), 400

    project = Project(name=name, description=description)
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@api.route('/projects', methods=['GET'])
def get_projects():
    projects =  Project.query.order_by(Project.id.asc()).all()
    return jsonify([project.to_dict() for project in projects])


@api.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.get_json() or {}
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    name = (data.get('name') or "").strip()
    description = (data.get('description') or "").strip()

    if name:
        project.name = name
    project.description = description
    db.session.commit()
    return jsonify(project.to_dict())


@api.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    req_ids = db.session.query(Requirement.id).filter(Requirement.project_id == project_id)
    db.session.query(Link).filter(
        (Link.source_requirement_id.in_(req_ids))
        | (Link.target_requirement_id.in_(req_ids))
    ).delete(synchronize_session=False)
    db.session.query(Requirement).filter(Requirement.project_id == project_id).delete(synchronize_session=False)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'})


@api.route('/projects/<int:project_id>/requirements', methods=['GET'])
def get_requirements(project_id):
    """Все требования со связями."""
    return jsonify(logic.get_all_requirements_with_links(project_id))


@api.route('/projects/<int:project_id>/requirements/<int:requirement_id>', methods=['GET'])
def get_requirement(project_id, requirement_id):
    req = logic.get_requirement_with_links(project_id, requirement_id)
    if req:
        return jsonify(req)
    return jsonify({'error': 'Requirement not found'}), 404


@api.route('/projects/<int:project_id>/requirements', methods=['POST'])
def create_requirement(project_id):
    """Создание требования."""
    data = request.json or {}

    try:
        requirement_data = {
            'title': data.get('title'),
            'description': data.get('description', ''),
            'requirement_type': RequirementType(data.get('requirement_type')),
            'status': RequirementStatus(data.get('status', 'Черновик')),
            'priority': Priority(data.get('priority', 'Средний')),
            'source': data.get('source', ''),
            'author': data.get('author', '')
        }

        req = logic.create_requirement(project_id, requirement_data, author=data.get('author') )
        return jsonify(req.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api.route('/projects/<int:project_id>/requirements/<int:requirement_id>', methods=['PUT'])
def update_requirement(project_id, requirement_id):
    """Обновление требования."""
    data = request.json or {}

    try:
        fields = {}

        if 'title' in data:
            fields['title'] = data['title']
        if 'description' in data:
            fields['description'] = data['description']
        if 'requirement_type' in data:
            fields['requirement_type'] = RequirementType(data['requirement_type'])
        if 'status' in data:
            fields['status'] = RequirementStatus(data['status'])
        if 'priority' in data:
            fields['priority'] = Priority(data['priority'])
        if 'source' in data:
            fields['source'] = data['source']
        if 'author' in data:
            fields['author'] = data['author']

        req = logic.update_requirement(project_id, requirement_id, fields, changed_by=data.get('changed_by'))
        if req:
            return jsonify(req.to_dict())
        return jsonify({'error': 'Requirement not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api.route('/projects/<int:project_id>/requirements/<int:requirement_id>', methods=['DELETE'])
def delete_requirement(project_id, requirement_id):
    """Удаление требования."""
    data = request.get_json(silent=True) or {}

    if logic.delete_requirement(project_id, requirement_id, deleted_by=data.get('deleted_by')):
        return jsonify({'message': 'Requirement deleted successfully'})

    return jsonify({'error': 'Requirement not found'}), 404


@api.route('/projects/<int:project_id>/requirements/<int:requirement_id>/history', methods=['GET'])
def get_requirement_history(project_id, requirement_id):
    """История изменения требования."""
    req = db.session.get(Requirement, requirement_id)
    if not req or req.project_id != project_id:
        return jsonify({'error': 'Requirement not found'}), 404
    history = logic.get_history(requirement_id)
    return jsonify([h.to_dict() for h in history])


@api.route('/projects/<int:project_id>/links', methods=['POST'])
def create_link(project_id):
    """Создание связи между требованиями."""
    data = request.json or {}

    try:
        link = logic.create_link(
            project_id = project_id,
            source_id=data['source_id'],
            target_id=data['target_id'],
            link_type=LinkType(data['link_type'])
        )

        if link:
            return jsonify(link.to_dict()), 201
        return jsonify({'error': 'Invalid link data'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api.route('/links/<int:link_id>', methods=['DELETE'])
def delete_link(link_id):
    """Удаление связи."""
    if logic.delete_link(link_id):
        return jsonify({'message': 'Link deleted successfully'})
    return jsonify({'error': 'Link not found'}), 404


@api.route('/projects/<int:project_id>/matrix', methods=['GET'])
def get_requirements_matrix(project_id):
    """Матрица пересечений требований."""
    reqs, matrix, _links = logic.build_matrix(project_id)
    return jsonify({'requirements': [r.to_dict() for r in reqs], 'matrix': matrix})


@api.route('/projects/<int:project_id>/export', methods=['GET'])
def export_to_excel(project_id):
    """Экспорт требований и связей в Excel."""
    reqs, _matrix, links = logic.build_matrix(project_id)

    exporter = ExportService()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_file.close()

    exporter.export_to_excel(reqs, links, temp_file.name)

    return send_file(
        temp_file.name,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='requirements_trace.xlsx'
    )


@api.route('/projects/<int:project_id>/export/matrix', methods=['GET'])
def export_matrix_to_excel(project_id):
    """Экспорт матрицы пересечений в Excel."""
    reqs, _matrix, links = logic.build_matrix(project_id)

    exporter = ExportService()

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_file.close()

    exporter.export_matrix_to_excel(reqs, links, temp_file.name)

    return send_file(
        temp_file.name,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='requirements_matrix.xlsx'
    )
