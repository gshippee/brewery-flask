import os
from flask import Flask
from flask_socketio import SocketIO
socketio = SocketIO()


def create_app(debug=True):
    """Create an application."""
    app = Flask(__name__, instance_relative_config=True)
    app.debug = debug
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'brewery.sqlite'),
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path,'../app/static/brew_instructions/')

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .main import db
    print('Initiating database')
    db.init_app(app)

    socketio.init_app(app, cors_allowed_origins='*')
    return app