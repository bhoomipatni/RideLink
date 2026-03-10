from sqlalchemy import Boolean, Float, create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Float, Boolean
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
    id = Column(Integer, primary_key=True) # postgreSQL uses serial so no need for autoincrement
    isdriver = Column(Boolean, nullable=False, default=False)
    rcsid = Column(String(50), unique=True, nullable=False)

class Rides(Base):
    __tablename__ = 'Rides'
    id = Column(Integer, primary_key=True,)  # postgreSQL uses serial so no need for autoincrement
    driverid = Column(Integer, nullable=False) # this is just rcsid
    address = Column(String(200), nullable=False)
    cost = Column(Float, nullable=False, default=0.0)
    isactive = Column(Boolean, default=True, nullable=False)
    description = Column(String(500), nullable=True)
    date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    

# create all tables
Base.metadata.create_all(engine)


