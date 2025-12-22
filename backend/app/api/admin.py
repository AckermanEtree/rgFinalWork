from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import User, Post, Comment, Rating
from ..utils.auth import is_admin
from ..utils.response import ok, error

bp = Blueprint("admin", __name__)


@bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    if not is_admin():
        return error("admin required", status=403)
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    items = [user.to_dict() for user in pagination.items]
    return ok({"items": items, "page": page, "per_page": per_page, "total": pagination.total})


@bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    if not is_admin():
        return error("admin required", status=403)
    user = User.query.get(user_id)
    if not user:
        return error("user not found", status=404)
    db.session.delete(user)
    db.session.commit()
    return ok({"user_id": user_id}, message="deleted")


@bp.route("/posts", methods=["GET"])
@jwt_required()
def list_posts_admin():
    if not is_admin():
        return error("admin required", status=403)
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    items = [post.to_dict() for post in pagination.items]
    return ok({"items": items, "page": page, "per_page": per_page, "total": pagination.total})


@bp.route("/posts/<int:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post_admin(post_id):
    if not is_admin():
        return error("admin required", status=403)
    post = Post.query.get(post_id)
    if not post:
        return error("post not found", status=404)
    db.session.delete(post)
    db.session.commit()
    return ok({"post_id": post_id}, message="deleted")


@bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    if not is_admin():
        return error("admin required", status=403)
    return ok(
        {
            "users": User.query.count(),
            "posts": Post.query.count(),
            "comments": Comment.query.count(),
            "ratings": Rating.query.count(),
        }
    )
