from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

Base = declarative_base()


# User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False) # For predefined admin

    reservations = relationship('Reservation', back_populates='user')

# Parking Lot model
class ParkingLot(Base):
    __tablename__ = 'parking_lots'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    amenities = Column(String)
    pricing = Column(Integer, default=10)  # e.g., per hour
    spots = relationship('ParkingSpot', back_populates='lot')


# Parking Spot model
class ParkingSpot(Base):
    __tablename__ = 'parking_spots'
    id = Column(Integer, primary_key=True)
    spot_number = Column(String, nullable=False)
    spot_type = Column(String)
    status = Column(String, default='available')  # available, occupied, reserved
    lot_id = Column(Integer, ForeignKey('parking_lots.id'))

    lot = relationship('ParkingLot', back_populates='spots')
    reservations = relationship('Reservation', back_populates='spot')

# Reservation model
class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    spot_id = Column(Integer, ForeignKey('parking_spots.id'))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String, default='active')  # active, cancelled, completed
    cost = Column(Integer)  # Add this line to store parking cost

    user = relationship('User', back_populates='reservations')
    spot = relationship('ParkingSpot', back_populates='reservations')


__all__ = [
    'Base',
    'User',
    'ParkingLot',
    'ParkingSpot',
    'Reservation'
]