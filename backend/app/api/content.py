from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_jwt_extended import get_jwt

from ..extensions import db
from ..models import Post, Tag, Media, Comment, Rating
from ..utils.response import ok, error

bp = Blueprint("content", __name__)


def _get_pagination(args, default_per_page=10):
    try:
        page = int(args.get("page", 1))
        per_page = int(args.get("per_page", default_per_page))
    except (TypeError, ValueError):
        return 1, default_per_page
    return max(page, 1), max(1, min(per_page, 100))


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@bp.route("/posts", methods=["POST"])
@jwt_required()
def create_post():
    payload = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    content = payload.get("content")
    visibility = payload.get("visibility", "public")
    tags = payload.get("tags") or []
    media_list = payload.get("media") or []

    post = Post(user_id=user_id, content=content, visibility=visibility)

    for name in tags:
        if not name:
            continue
        tag = Tag.query.filter_by(name=name).first()
        if not tag:
            tag = Tag(name=name)
        post.tags.append(tag)

    for item in media_list:
        if not isinstance(item, dict):
            continue
        media_type = item.get("type")
        url = item.get("url")
        if not media_type or not url:
            continue
        media = Media(type=media_type, url=url, thumbnail_url=item.get("thumbnail_url"))
        post.media_items.append(media)

    db.session.add(post)
    db.session.commit()
    return ok({"post": post.to_dict()}, message="created", status=201)


@bp.route("/posts", methods=["GET"])
def list_posts():
    args = request.args
    tag = args.get("tag")
    user_id = args.get("user_id")
    start_date = _parse_datetime(args.get("start_date"))
    end_date = _parse_datetime(args.get("end_date"))
    page, per_page = _get_pagination(args)

    query = Post.query
    if user_id:
        query = query.filter(Post.user_id == user_id)
    if tag:
        query = query.join(Post.tags).filter(Tag.name == tag)
    if start_date:
        query = query.filter(Post.created_at >= start_date)
    if end_date:
        query = query.filter(Post.created_at <= end_date)

    pagination = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    posts = [post.to_dict() for post in pagination.items]
    return ok(
        {
            "items": posts,
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
        }
    )


@bp.route("/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return error("post not found", status=404)
    return ok({"post": post.to_dict()})


@bp.route("/posts/<int:post_id>", methods=["PUT"])
@jwt_required()
def update_post(post_id):
    payload = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    role = get_jwt().get("role")
    post = Post.query.get(post_id)
    if not post:
        return error("post not found", status=404)
    if post.user_id != user_id and role != "admin":
        return error("forbidden", status=403)

    content = payload.get("content")
    visibility = payload.get("visibility")
    tags = payload.get("tags")
    media_list = payload.get("media")

    if content is not None:
        post.content = content
    if visibility:
        post.visibility = visibility

    if tags is not None:
        post.tags = []
        for name in tags:
            if not name:
                continue
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
            post.tags.append(tag)

    if media_list is not None:
        post.media_items = []
        for item in media_list:
            if not isinstance(item, dict):
                continue
            media_type = item.get("type")
            url = item.get("url")
            if not media_type or not url:
                continue
            media = Media(type=media_type, url=url, thumbnail_url=item.get("thumbnail_url"))
            post.media_items.append(media)

    db.session.commit()
    return ok({"post": post.to_dict()}, message="updated")


@bp.route("/posts/<int:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    user_id = get_jwt_identity()
    role = get_jwt().get("role")
    post = Post.query.get(post_id)
    if not post:
        return error("post not found", status=404)
    if post.user_id != user_id and role != "admin":
        return error("forbidden", status=403)

    db.session.delete(post)
    db.session.commit()
    return ok({"post_id": post_id}, message="deleted")


@bp.route("/posts/<int:post_id>/comments", methods=["POST"])
@jwt_required()
def create_comment(post_id):
    payload = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    if not post:
        return error("post not found", status=404)
    content = (payload.get("content") or "").strip()
    if not content:
        return error("content required", status=400)

    comment = Comment(post_id=post_id, user_id=user_id, content=content)
    db.session.add(comment)
    db.session.commit()
    return ok({"comment": comment.to_dict()}, message="created", status=201)


@bp.route("/posts/<int:post_id>/comments", methods=["GET"])
def list_comments(post_id):
    post = Post.query.get(post_id)
    if not post:
        return error("post not found", status=404)
    page, per_page = _get_pagination(request.args)
    pagination = (
        Comment.query.filter_by(post_id=post_id)
        .order_by(Comment.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    items = [comment.to_dict() for comment in pagination.items]
    return ok(
        {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
        }
    )


@bp.route("/posts/<int:post_id>/ratings", methods=["POST"])
@jwt_required()
def create_rating(post_id):
    payload = request.get_json(silent=True) or {}
    user_id = get_jwt_identity()
    post = Post.query.get(post_id)
    if not post:
        return error("post not found", status=404)
    score = payload.get("score")
    try:
        score = int(score)
    except (TypeError, ValueError):
        return error("score must be an integer", status=400)
    if score < 1 or score > 5:
        return error("score must be between 1 and 5", status=400)

    rating = Rating.query.filter_by(post_id=post_id, user_id=user_id).first()
    if rating:
        rating.score = score
    else:
        rating = Rating(post_id=post_id, user_id=user_id, score=score)
        db.session.add(rating)

    db.session.commit()
    return ok({"rating": rating.to_dict()}, message="saved", status=201)
