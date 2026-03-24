from sqlalchemy.dialects.postgresql import ARRAY

from sqlalchemy import Boolean, Float, ForeignKey, create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Float, Boolean
from sqlalchemy.orm import relationship
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

# update postgres address as needed
database_url = os.getenv('DATABASE_URL')

if not database_url:
    raise RuntimeError("DATABASE_URL environment variable is not set. Please configure DATABASE_URL before starting the application.")
engine = create_engine(database_url)

# example model
class User(Base):
    __tablename__ = 'Users'
    isdriver = Column(Boolean, nullable=False, default=False)
    rcsid = Column(String(50), primary_key=True, unique=True, nullable=False)
    rides = Column(ARRAY(Integer), nullable=True) # this is just a list of ride ids, can be null if no rides

    password = Column(String(100), nullable=False)
    payment_methods = relationship("PaymentMethods", backref="user", uselist=False)
    
class Rides(Base):
    __tablename__ = 'Rides'
    id = Column(Integer, primary_key=True,)  # postgreSQL uses serial so no need for autoincrement
    driverid = Column(String(200), nullable=False)
    address = Column(String(200), nullable=False)
    orgin = Column(String(200), nullable=False)
    cost = Column(Float, nullable=False, default=0.0)
    isactive = Column(Boolean, default=True, nullable=False)
    description = Column(String(500), nullable=True)
    date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column("long", Float, nullable=False)

class PaymentMethods(Base):
    __tablename__ = "PaymentMethods"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), ForeignKey('Users.rcsid'), nullable=False)
    
    venmo_username = Column(String(50), nullable=True)
    paypal_email = Column(String(100), nullable=True)
    accepts_cash = Column(Boolean, default=False)

    # Optional: track when it was last updated
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now)
    riders = Column(ARRAY(String(50)), nullable=True) # this is just a list of rider rcsids, can be null if no riders

    

# create all tables
Base.metadata.create_all(engine)


