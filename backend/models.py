from sqlalchemy import Boolean, Float, create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

# update postgres address as needed
database_url = 'postgresql://username:password@host/database_name'

# Create an engine
engine = create_engine(database_url)

Base = declarative_base()

# example model
class User(Base):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True) # postgreSQL uses serial so no need for autoincrement
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    rcsid = Column(String(20), unique=True, nullable=False)

class Rides(Base):
    __tablename__ = 'Rides'
    id = Column(Integer, primary_key=True,)  # postgreSQL uses serial so no need for autoincrement
    driverid = Column(Integer, nullable=False)
    address = Column(String(200), nullable=False)
    cost = Column(Float, nullable=False, default=0.0)
    isactive = Column(Boolean, default=True, nullable=False)
    description = Column(String(500), nullable=True)
    date = Column(DateTime, default=datetime.datetime.now, nullable=False)

    

# create all tables
Base.metadata.create_all(engine)


