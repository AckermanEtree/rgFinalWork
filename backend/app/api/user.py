from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import User
from ..utils.response import ok, error

bp = Blueprint("user", __name__)


@bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error("user not found", status=404)
    return ok({"user": user.to_dict()})


@bp.route("/me", methods=["PUT"])
@jwt_required()
def update_me():
    payload = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error("user not found", status=404)

    username = payload.get("username")
    avatar = payload.get("avatar")
    password = payload.get("password")

    if username:
        username = username.strip()
        if not username:
            return error("username cannot be empty", status=400)
        exists = User.query.filter(User.username == username, User.id != user.id).first()
        if exists:
            return error("username already exists", status=409)
        user.username = username

    if avatar is not None:
        user.avatar = avatar

    if password:
        user.set_password(password)

    db.session.commit()
    return ok({"user": user.to_dict()}, message="updated")
