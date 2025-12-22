from ..extensions import db


class Media(db.Model):
    __tablename__ = "media"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    type = db.Column(db.String(16), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    thumbnail_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    post = db.relationship("Post", back_populates="media_items")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
        }
