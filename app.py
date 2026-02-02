from flask import Flask, render_template, abort
from sqlalchemy import inspect, text

from config import Config
from database import db
from api.routes import api
from models.project import Project

app = Flask(__name__)
app.config.from_object(Config)

# База
db.init_app(app)

# API ручки
app.register_blueprint(api, url_prefix='/api')

def ensure_project_id_column():
    inspector = inspect(db.engine)
    if 'requirements' not in inspector.get_table_names():
        return

    columns = [col['name'] for col in inspector.get_columns('requirements')]
    if 'project_id' in columns:
        return

    with db.engine.begin() as conn:
        conn.execute(text("ALTER TABLE requirements ADD COLUMN project_id INTEGER"))

    project = Project.query.order_by(Project.id.asc()).first()
    if not project:
        project = Project(name="Default project", description="Auto-created project")
        db.session.add(project)
        db.session.commit()

    db.session.execute(
        text("UPDATE requirements SET project_id = :project_id WHERE project_id IS NULL"),
        {"project_id": project.id},
    )
    db.session.commit()


@app.route('/')
def index():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('login.html')


@app.route('/project/<int:project_id>')
def project_home(project_id: int):
    project = Project.query.get(project_id)
    if not project:
        abort(404)
    return render_template('index.html', project=project)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_project_id_column()

    app.run(debug=True)
