import os
from flask import Flask, send_from_directory

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

    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    if not os.path.isabs(upload_folder):
        upload_folder = os.path.abspath(os.path.join(app.root_path, "..", upload_folder))
    app.config["UPLOAD_FOLDER"] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(upload_folder, filename)

    register_blueprints(app)
    from . import models  # noqa: F401

    return app
