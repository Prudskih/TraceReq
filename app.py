from flask import Flask, render_template

from config import Config
from database import db
from api.routes import api


app = Flask(__name__)
app.config.from_object(Config)

# База
db.init_app(app)

# API ручки
app.register_blueprint(api, url_prefix='/api')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
