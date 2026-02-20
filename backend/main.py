
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from backend import models
from backend.models import engine
from sqlalchemy.orm import sessionmaker, Session
import datetime

app = FastAPI()

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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


# Pydantic models
class RideRequest(BaseModel):
    driverid: int
    address: str
    cost: float
    description: str | None = None
    lat: float
    long: float

class putUser(BaseModel):
    username: str
    email: str
    rcsid: str
    isdriver: bool
    password: str

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"result": item_id,}


@app.get("/rides/{ride_id}")
def read_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(models.Rides).filter_by(id=ride_id).first()
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
        raise HTTPException(status_code=404, detail="Ride not found")

@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if user:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "rcsid": user.rcsid,
            "password": user.password,
        }
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.post("/request_ride")
def request_ride(ride: RideRequest, db: Session = Depends(get_db)):
    new_ride = models.Rides(
        driverid=ride.driverid,
        address=ride.address,
        cost=ride.cost,
        description=ride.description,
        date=datetime.datetime.now(datetime.timezone.utc),
        lat=ride.lat,
        long=ride.long,
    )
    try:
        db.add(new_ride)
        db.commit()
        db.refresh(new_ride)
        return new_ride
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/add_user")
def add_user(user: putUser, db: Session = Depends(get_db)):
    new_user = models.User(
        username=user.username,
        email=user.email,
        rcsid=user.rcsid,
        password=user.password
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))