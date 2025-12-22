from flask import Blueprint, request
from flask_jwt_extended import create_access_token

from ..extensions import db
from ..models import User
from ..utils.response import ok, error

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if not username or not password:
        return error("username and password required", status=400)

    exists = User.query.filter_by(username=username).first()
    if exists:
        return error("username already exists", status=409)

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return ok({"user": user.to_dict()}, message="registered", status=201)


@bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if not username or not password:
        return error("username and password required", status=400)

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return error("invalid credentials", status=401)

    access_token = create_access_token(
        identity=str(user.id), additional_claims={"role": user.role}
    )
    return ok({"access_token": access_token, "user": user.to_dict()}, message="logged in")
