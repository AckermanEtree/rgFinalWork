from ..extensions import db


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text)
    visibility = db.Column(db.String(16), default="public", nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    author = db.relationship("User", back_populates="posts")
    media_items = db.relationship("Media", back_populates="post", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    ratings = db.relationship("Rating", back_populates="post", cascade="all, delete-orphan")
    tags = db.relationship("Tag", secondary="post_tags", back_populates="posts")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.author.username if self.author else None,
            "avatar": self.author.avatar if self.author else None,
            "content": self.content,
            "visibility": self.visibility,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": [tag.name for tag in self.tags],
            "media": [media.to_dict() for media in self.media_items],
        }
