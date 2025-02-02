from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Bike(db.Model):
    __tablename__ = 'bikes'

    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    available_units = Column(Integer, default=1)

    # Relationships
    rentals = relationship("Rental", back_populates="bike", cascade="all, delete-orphan")
    waitinglist = relationship("WaitingList", back_populates="bike", cascade="all, delete-orphan")

    def __init__(self, model, brand, serial_number, available_units=1):
        self.model = model
        self.brand = brand
        self.serial_number = serial_number
        self.available_units = available_units

    def __repr__(self):
        return f'<Bike {self.model} - {self.brand}>'


class Rental(db.Model):
    __tablename__ = 'rentals'

    id = Column(Integer, primary_key=True)
    bike_id = Column(Integer, ForeignKey('bikes.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    rented_on = Column(DateTime, default=datetime.utcnow)
    return_by = Column(DateTime, nullable=True)
    returned_on = Column(DateTime, nullable=True)
    event_processed = Column(Integer, default=0)  # 0 = Not processed, 1 = Processed

    # Relationship to Bike
    bike = relationship("Bike", back_populates="rentals")

    def __init__(self, bike_id, user_id, return_by):
        self.bike_id = bike_id
        self.user_id = user_id
        self.return_by = return_by

    def __repr__(self):
        return f'<Rental {self.bike.model} by User {self.user_id}>'


class WaitingList(db.Model):
    __tablename__ = 'waitinglist'

    id = Column(Integer, primary_key=True)
    bike_id = Column(Integer, ForeignKey('bikes.id'), nullable=False)
    user_id = Column(Integer, nullable=False)
    status = Column(String(50), default='waiting')  # 'waiting' or 'notified'

    # Relationship to Bike
    bike = relationship("Bike", back_populates="waitinglist")

    def __init__(self, bike_id, user_id):
        self.bike_id = bike_id
        self.user_id = user_id

    def __repr__(self):
        return f'<WaitingList for {self.bike.model} - User {self.user_id}>'
