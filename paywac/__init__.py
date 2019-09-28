from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from paywac.config import Config
from datetime import timedelta


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config) 

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    app.config['TESTING'] = False

    from paywac.users.routes import users
    from paywac.main.routes import main
    from paywac.contracts.routes import contracts

    app.register_blueprint(users)
    app.register_blueprint(main)
    app.register_blueprint(contracts)

    app.jinja_env.filters['from_seconds_to_time'] = from_seconds_to_time

    return app

def from_seconds_to_time(s):
    return timedelta(seconds=s)