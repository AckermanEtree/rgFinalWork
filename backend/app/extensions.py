from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Extension instances are initialized in app factory

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()
