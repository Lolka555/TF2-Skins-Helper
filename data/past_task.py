import sqlalchemy
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class UserHistory(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users_history'

    userId = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    tasks = sqlalchemy.Column(sqlalchemy.String)