from ..extensions import db


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    posts = db.relationship("Post", secondary="post_tags", back_populates="tags")

    def to_dict(self):
        return {"id": self.id, "name": self.name}
