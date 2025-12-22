import os
from flask import Flask

from .extensions import db, migrate, cors, jwt
from .api import register_blueprints


def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=False)

    if config_object:
        app.config.from_object(config_object)
    else:
        config_name = os.getenv("FLASK_CONFIG", "development")
        app.config.from_object(f"config.{config_name.capitalize()}Config")

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    jwt.init_app(app)

    register_blueprints(app)
    from . import models  # noqa: F401

    return app
