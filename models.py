from app import db
from sqlalchemy.dialects.postgresql import JSON


class Result(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String())
    category = db.Column(db.String())

    def __init__(self, url, category):
        self.url = url
        self.category = category

    def __repr__(self):
        return '<id {}>'.format(self.id)