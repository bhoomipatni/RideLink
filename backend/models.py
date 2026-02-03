from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

# update postgres address as needed
database_url = 'postgresql://username:password@host/database_name'

# Create an engine
engine = create_engine(database_url)

Base() = declarative_base()

# example model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)

# create all tables
Base.metadata.create_all(engine)

# insert the data into database and start a session
Session = sessionmaker(bind=engine)
session = Session()

# insert a user to the table during the session
# ALWAYS COMMIT WHEN YOU ARE ADDING OR EDITING DATA IN THE DATABASE OR CHANGES WILL NOT BE SAVED
new_user = User(username='Sandy', email='sandy@gmail.com', password='cool-password')
session.add(new_user)
session.commit()

# THESE ARE PURELY EXAMPLES OF HOW TO QUERY THE DATABASE WE WILL PROBABLY BE DOING QUERIES IN main.py OR ANOTHER FILE
# AND LEAVE THIS FILE PURELY FOR THE MODELS AND DATABASE CONNECTION
# Example: query some data from the database and print
all_users = session.query(User).all()
for user in all_users:
    print(user.username, user.email)

# Example: Querying a specific user by their username
user = session.query(User).filter_by(username='Sandy').first()
print(user.username)

# close the session
session.close()