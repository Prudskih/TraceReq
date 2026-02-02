from flask import Flask, render_template, abort

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

    app.run(debug=True)
