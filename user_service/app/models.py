from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'user' or 'admin'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    # watched_bikes = relationship("WatchedBike", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, username, name, role):
        self.username = username
        self.name = name
        self.role = role

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

#
# class WatchedBike(db.Model):
#     __tablename__ = 'watched_bikes'
#
#     id = Column(Integer, primary_key=True)
#     bike_id = Column(Integer, nullable=False)  # Store only bike_id, no direct relationship
#     watched_on = Column(DateTime, default=datetime.utcnow)
#     user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
#
#     # Relationship to User
#     user = relationship("User", back_populates="watched_bikes")
#
#     def __init__(self, bike_id, user_id):
#         self.bike_id = bike_id
#         self.user_id = user_id
#
#     def __repr__(self):
#         return f'<WatchedBike {self.bike_id} by {self.user.username}>'
