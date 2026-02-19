
from fastapi import FastAPI
from pydantic import BaseModel
from backend import models
from backend.models import engine
from sqlalchemy.orm import sessionmaker
import datetime

app = FastAPI()
# insert the data into database and start a session
Session = sessionmaker(bind=engine)
session = Session()

# Example database query to ensure models are loaded
# users = session.query(models.User).all()

# insert a user to the table during the session
# ALWAYS COMMIT WHEN YOU ARE ADDING OR EDITING DATA IN THE DATABASE OR CHANGES WILL NOT BE SAVED
# new_user = models.User(username='Sandy', email='sandy@gmail.com', password='cool-password')
# models.session.add(new_user)
# models.session.commit()

# THESE ARE PURELY EXAMPLES OF HOW TO QUERY THE DATABASE WE WILL PROBABLY BE DOING QUERIES IN main.py OR ANOTHER FILE
# AND LEAVE THIS FILE PURELY FOR THE MODELS AND DATABASE CONNECTION
# Example: query some data from the database and print
# all_users = session.query(User).all()
# for user in all_users:
#     print(user.username, user.email)

# Example: Querying a specific user by their username
# user = session.query(User).filter_by(username='Sandy').first()
# print(user.username)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"result": item_id,}


@app.get("/rides/{ride_id}")
def read_ride(ride_id: int):
    ride = session.query(models.Rides).filter_by(id=ride_id).first()
    if ride:
        return {
            "id": ride.id,
            "driverid": ride.driverid,
            "address": ride.address,
            "cost": ride.cost,
            "isactive": ride.isactive,
            "description": ride.description,
            "date": ride.date.isoformat(),
            "lat": ride.lat,
            "long": ride.long,
        }
    else:
        return {"error": "Ride not found"}, 404

class RideRequest(BaseModel):
    driverid: int
    address: str
    cost: float
    description: str | None = None
    lat: float
    long: float


@app.post("/request_ride")
def request_ride(ride: RideRequest):
    new_ride = models.Rides(
        driverid=ride.driverid,
        address=ride.address,
        cost=ride.cost,
        description=ride.description,
        date=datetime.datetime.now(datetime.timezone.utc),
        lat=ride.lat,
        long=ride.long,
    )
    session.add(new_ride)
    session.commit()
    session.refresh(new_ride)
    return new_ride