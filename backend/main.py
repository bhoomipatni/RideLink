
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from backend import models
from backend.models import engine
from sqlalchemy.orm import sessionmaker, Session
import datetime
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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
            "lon": ride.lon,
        }
    else:
        raise HTTPException(status_code=404, detail="Ride not found")

# ride search by address
# get from json
with open(os.path.join(os.path.dirname(__file__), "params.json")) as f:
    _params = json.load(f)
DISTANCE_LIMIT = _params["DISTANCE_LIMIT"] # how far away do we set teh bounding box
GET_ETA_COUNT = _params["GET_ETA_COUNT"] # how many candidates do we send to the API to get ETAs for 
# end point example GET /search_rides/123%20Main%20St/2024-06-01T12:00:00Z  where its a str address and an iso date
@app.get("/search_rides/{address}/{date}")
def search_rides(address: str, date: str, db: Session = Depends(get_db)):
    # makie a bounding box around the address using lat and lon are threshold in the const above
    # get lat/lon from address using Google Geocoding API
    geo = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": address, "key": GOOGLE_API_KEY}
    ).json()
    if geo.get("status") != "OK" or not geo.get("results"):
        raise HTTPException(status_code=400, detail="Address not found")
    print(geo)
    if not geo["results"]:
        raise HTTPException(status_code=400, detail="Address not found")
    location = geo["results"][0]["geometry"]["location"]
    lat, lon = location["lat"], location["lng"]
    print(f"Searching for rides near {address} at lat {lat} and lon {lon}")
    min_lat = lat - DISTANCE_LIMIT
    max_lat = lat + DISTANCE_LIMIT
    min_lon = lon - DISTANCE_LIMIT
    max_lon = lon + DISTANCE_LIMIT
    # then query the database for rides within the bounding box and are within 24 hours of the request date both ways
    rides = db.query(models.Rides).filter(
        models.Rides.lat >= min_lat,
        models.Rides.lat <= max_lat,
        models.Rides.lon >= min_lon,
        models.Rides.lon <= max_lon,
        models.Rides.isactive == True,
        models.Rides.date >= datetime.datetime.fromisoformat(date) - datetime.timedelta(hours=24),
        models.Rides.date <= datetime.datetime.fromisoformat(date) + datetime.timedelta(hours=24),
    ).all()
    # sort rides by distance to address in degrees so we can get the top to send to the API
    rides.sort(key=lambda r: (r.lat - lat)**2 + (r.lon - lon)**2)
    rides = rides[:GET_ETA_COUNT]
    if not rides:
        raise HTTPException(status_code=404, detail="No rides found")
    # batch Distance Matrix API call to get ETAs from each ride origin to the user address
    destinations = [{"waypoint": {"location": {"latLng": {"latitude": r.lat, "longitude": r.lon}}}} for r in rides]
    matrix_resp = requests.post(
        "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
        headers={
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status"
        },
        json={
            "origins": [{"waypoint": {"location": {"latLng": {"latitude": lat, "longitude": lon}}}}],
            "destinations": destinations,
            "travelMode": "DRIVE", # we can change this down the line
            "routingPreference": "TRAFFIC_AWARE"
        }
    ).json()
    # make the dict
    eta_map = {entry["destinationIndex"]: int(entry["duration"].replace("s", "")) for entry in matrix_resp if "duration" in entry}
    # sort by eta
    rides_with_eta = sorted(
        [{"ride": r, "eta_seconds": eta_map.get(i)} for i, r in enumerate(rides)],
        key=lambda x: x["eta_seconds"] if x["eta_seconds"] is not None else float("inf")
    )
    return rides_with_eta
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
    # get lat and lon from address using Google Geocoding API
    geo = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": ride.address, "key": GOOGLE_API_KEY}
    ).json()
    if not geo["results"]:
        raise HTTPException(status_code=400, detail="Address not found")
    location = geo["results"][0]["geometry"]["location"]
    lat, lon = location["lat"], location["lng"]
    new_ride = models.Rides(
        driverid=ride.driverid,
        address=ride.address,
        cost=ride.cost,
        description=ride.description,
        date=datetime.datetime.now(datetime.timezone.utc),
        lat=lat,
        lon=lon,
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
        password=user.password,
        isdriver=user.isdriver
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
