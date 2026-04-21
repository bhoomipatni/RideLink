from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, ConfigDict
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend import models
from backend.models import engine
from sqlalchemy.orm import sessionmaker, Session
from .models import User, Rides, Base, engine
import datetime
import json
import os
import requests
from dotenv import load_dotenv
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.metadata import OneLogin_Saml2_Metadata
import jwt
from apscheduler.schedulers.background import BackgroundScheduler
from backend.check_rides import expire_old_rides

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(expire_old_rides, "interval", minutes=5, next_run_time=datetime.datetime.now())
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Load SAML settings for auth endpoints on this main app.
with open(os.path.join(os.path.dirname(__file__), "config", "settings.json")) as f:
    saml_settings = json.load(f)

saml_private_key = os.getenv("SAML_PRIVATE_KEY")
if not saml_private_key:
    raise RuntimeError("SAML_PRIVATE_KEY is not set in environment")
saml_settings["sp"]["privateKey"] = saml_private_key.replace("\\n", "\n")

with open(os.path.join(os.path.dirname(__file__), "keys", "server.crt")) as f:
    saml_settings["sp"]["x509cert"] = f.read()

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_saml_auth(req):
    return OneLogin_Saml2_Auth(req, saml_settings)


def validate_sp_metadata(metadata_xml: str):
    """Handle python3-saml validator naming differences across versions."""
    if hasattr(OneLogin_Saml2_Metadata, "validate_metadata"):
        return OneLogin_Saml2_Metadata.validate_metadata(metadata_xml)
    if hasattr(OneLogin_Saml2_Metadata, "validateMetadata"):
        return OneLogin_Saml2_Metadata.validateMetadata(metadata_xml)
    return []


async def prepare_saml_request(request: Request):
    return {
        "http_host": request.url.hostname,
        "script_name": str(request.url.path),
        "server_port": request.url.port or 80,
        "get_data": dict(request.query_params),
        "post_data": dict(await request.form()) if request.method == "POST" else {},
        "https": "on" if request.url.scheme == "https" else "off",
    }


# Pydantic models
# driver posts a ride with address, cost, description
class RideRequest(BaseModel):
    driverid: str
    address: str
    origin: str
    cost: float
    description: str | None = None
    date: datetime.datetime | None = None

class RideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    driverid: str
    address: str
    origin: str
    cost: float
    isactive: bool
    description: str | None = None
    date: datetime.datetime
    lat: float
    lon: float

# adds a user to the database with username, rcsid, and isdriver boolean
class UserInput(BaseModel):
    username: str
    rcsid: str
    isdriver: bool
    rides: list[int] | None = None 

# returns json with user info
class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str
    rcsid: str
    isdriver: bool
    rides: list[int] | None = None

# this is response model for search function that returns a dict with ride info and eta in seconds to the ride
# maybe put config in here
class RideWithETA(BaseModel):
    ride: RideResponse
    detour_eta: int | None = None # time from the ride arriaval address to the users desired address
    # detour is a bad name but its just saying how long it would take if the driver doesnt help you get there
    true_eta: int | None = None # time from the ride orgin to the users desired address

# this is the response model for upcoming/previous rides
class RideListResponse(BaseModel):
    rides: list[RideResponse]

@app.get("/")
async def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/login")
async def login(request: Request):
    req = await prepare_saml_request(request)
    auth = init_saml_auth(req)
    return RedirectResponse(url=auth.login())


@app.post("/callback")
async def callback(request: Request):
    req = await prepare_saml_request(request)
    auth = init_saml_auth(req)
    auth.process_response()

    rcsid = auth.get_nameid()
    token = jwt.encode({"rcsid": rcsid}, os.getenv("SAML_PRIVATE_KEY"), algorithm="HS256")
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie("session", token)
    return response

def get_current_user(request: Request, db: Session = Depends(get_db)):
    # TEMPORARY OVERRIDE WITH HARDCODE — login is bugged, remove when fixed
    user = db.query(models.User).filter_by(rcsid="oyong").first()
    if not user:
        raise HTTPException(status_code=404, detail="Hardcoded dev user 'oyong' not found in DB")
    return user
    token = request.cookies.get("session")
    print(f"[get_current_user] session cookie present: {bool(token)}")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, os.getenv("SAML_PRIVATE_KEY"), algorithms=["HS256"])
        rcsid = str(payload["rcsid"])
        print(f"[get_current_user] decoded rcsid: {rcsid!r}")
    except jwt.PyJWTError as e:
        print(f"[get_current_user] JWT decode failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    if not rcsid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(models.User).filter_by(rcsid=rcsid).first()
    print(f"[get_current_user] user lookup result: {user}")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/metadata", response_class=HTMLResponse)
def metadata():
    metadata_xml = OneLogin_Saml2_Metadata.builder(saml_settings["sp"], None, True)
    errors = validate_sp_metadata(metadata_xml)
    if errors:
        return {"errors": errors}
    return HTMLResponse(content=metadata_xml, media_type="text/xml")

@app.get("/rides/{ride_id}")
def read_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(models.Rides).filter_by(id=ride_id).first()
    if ride:
        return RideResponse.model_validate(ride)
    else:
        raise HTTPException(status_code=404, detail="Ride not found")
    
@app.post("/rides/{ride_id}/add_rider")
def add_rider(ride_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ride = db.query(models.Rides).filter_by(id=ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    user = db.query(models.User).filter_by(rcsid=current_user.rcsid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.rides.append(ride.id)
    try:
        db.commit()
        db.refresh(ride)
        return RideResponse.model_validate(ride)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ride search by address
# get from json
with open(os.path.join(os.path.dirname(__file__), "params.json")) as f:
    _params = json.load(f)
DISTANCE_LIMIT = _params["DISTANCE_LIMIT"] # how far away do we set teh bounding box
GET_ETA_COUNT = _params["GET_ETA_COUNT"] # how many candidates do we send to the API to get ETAs for
ROUTING_PREF = "TRAFFIC_AWARE" if _params["TRAFFIC_AWARE"] else "TRAFFIC_UNAWARE"
# end point example GET /search_rides/123%20Main%20St/2024-06-01T12:00:00Z  where its a str address and an iso date
@app.get("/search_rides/{address}/{date}", response_model=list[RideWithETA])
def search_rides(address: str, date: str, db: Session = Depends(get_db)):
    # makie a bounding box around the address using lat and lon are threshold in the const above
    # get lat/lon from address using Google Geocoding API
    geo = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": address, "key": GOOGLE_API_KEY}
    ).json()
    if geo.get("status") != "OK" or not geo.get("results"):
        raise HTTPException(status_code=400, detail="Address not found")
    if not geo["results"]:
        raise HTTPException(status_code=400, detail="Address not found")
    location = geo["results"][0]["geometry"]["location"]
    lat, lon = location["lat"], location["lng"]
    min_lat = lat - DISTANCE_LIMIT
    max_lat = lat + DISTANCE_LIMIT
    min_lon = lon - DISTANCE_LIMIT
    max_lon = lon + DISTANCE_LIMIT
    parsed_date = datetime.datetime.fromisoformat(date)
    date_min = parsed_date - datetime.timedelta(hours=24)
    date_max = parsed_date + datetime.timedelta(hours=24)
    # then query the database for rides within the bounding box and are within 24 hours of the request date both ways
    rides = db.query(models.Rides).filter(
        models.Rides.lat >= min_lat,
        models.Rides.lat <= max_lat,
        models.Rides.lon >= min_lon,
        models.Rides.lon <= max_lon,
        models.Rides.isactive == True,
        models.Rides.date >= date_min,
        models.Rides.date <= date_max,
    ).all()
    # sort rides by distance to address in degrees so we can get the top to send to the API
    rides.sort(key=lambda r: (r.lat - lat)**2 + (r.lon - lon)**2)
    rides = rides[:GET_ETA_COUNT]
    if not rides:
        raise HTTPException(status_code=404, detail="No rides found")
    # batch Distance Matrix API call to get ETAs from each ride origin to the user address
    destinations = [{"waypoint": {"location": {"latLng": {"latitude": r.lat, "longitude": r.lon}}}} for r in rides]
    raw = requests.post(
        "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
        headers={
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status"
        },
        json={
            "origins": [{"waypoint": {"location": {"latLng": {"latitude": lat, "longitude": lon}}}}],
            "destinations": destinations,
            "travelMode": "DRIVE", # we can change this down the line
            "routingPreference": ROUTING_PREF
        }
    )
    matrix_resp = raw.json()
    # get each ride's overall ETA (origin -> address)
    trip_resp = requests.post(
        "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
        headers={
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": "originIndex,destinationIndex,duration,status"
        },
        json={
            "origins": [{"waypoint": {"address": r.origin}} for r in rides],
            "destinations": [{"waypoint": {"address": r.address}} for r in rides],
            "travelMode": "DRIVE",
            "routingPreference": ROUTING_PREF
        }
    ).json()
    # make the dict: detour_eta (user detour) + full_eta (ride origin->dest)
    eta_map = {}
    for i, r in enumerate(rides):
        eta_map[i] = {
            "detour_eta": next((int(float(e["duration"].rstrip("s"))) for e in matrix_resp if "duration" in e and e.get("destinationIndex", 0) == i), None),
            "true_eta": next((int(float(e["duration"].rstrip("s"))) for e in trip_resp if "duration" in e and e.get("originIndex", 0) == i and e.get("destinationIndex", 0) == i), None)
        }
    # sort by full_eta
    rides_with_eta = sorted(
        [RideWithETA(ride=RideResponse.model_validate(r), detour_eta=eta_map[i]["detour_eta"], true_eta=eta_map[i]["true_eta"]) for i, r in enumerate(rides)],
        key=lambda x: x.true_eta if x.true_eta is not None else float("inf")
    )
    return rides_with_eta


@app.get("/users/{user_id}")
def read_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(rcsid=user_id).first()
    if user:
        return UserOutput.model_validate(user)
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.post("/request_ride")
def request_ride(request: Request, ride: RideRequest, db: Session = Depends(get_db), user = Depends(get_current_user)):
    if not user.isdriver:
        raise HTTPException(status_code=403, detail="Register as a driver to post rides")
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
        origin =ride.origin,
        address=ride.address,
        cost=ride.cost,
        description=ride.description,
        date=ride.date,
        lat=lat,
        lon=lon,
        riders =[]
    )
    try:
        db.add(new_ride)
        db.commit()
        db.refresh(new_ride)
        if hasattr(request.app.state, "scheduler"):
            request.app.state.scheduler.add_job(expire_old_rides, "date", run_date=new_ride.date)
        return RideResponse.model_validate(new_ride)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/add_user")
def add_user(user: UserInput, db: Session = Depends(get_db)):
    new_user = models.User(
        username=user.username,
        rcsid=user.rcsid,
        isdriver=user.isdriver,
        rides=user.rides or []
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return UserOutput.model_validate(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/userid/{rcsid}")
def get_userid(rcsid: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(rcsid=rcsid).first()
    if user:
        return {"id": user.id}
    else:
        raise HTTPException(status_code=404, detail="User not found")
@app.get("/get_map")
def get_map():
    resp = requests.get(
        "https://maps.googleapis.com/maps/api/js",
        params={"key": GOOGLE_API_KEY, "libraries": "places", "callback": "initMap"}
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to load Maps API")
    from fastapi.responses import Response
    return Response(content=resp.text, media_type="application/javascript")

# returns current and any upcoming rides
@app.get("/upcoming_rides", response_model=RideListResponse)
def get_upcoming_rides(db: Session = Depends(get_db), user = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    rides = db.query(models.Rides).filter(
        models.Rides.date > datetime.datetime.now(datetime.timezone.utc),
        models.Rides.isactive == True).all()
    
    return RideListResponse(rides=rides or [])

# returns past rides that are no longer active
@app.get("/previous_rides", response_model=RideListResponse)
def get_previous_rides(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    user = db.query(models.User).filter_by(rcsid=current_user.rcsid).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    rides = db.query(models.Rides).filter(
        models.Rides.date < datetime.datetime.now(datetime.timezone.utc),
        models.Rides.isactive == False).all()

    return RideListResponse(rides=rides or [])

@app.get("/five_upcoming_rides", response_model=RideListResponse)
def five_upcoming_rides(db: Session = Depends(get_db)):
    rides = db.query(models.Rides).filter(
        models.Rides.date > datetime.datetime.now(datetime.timezone.utc),
        models.Rides.isactive == True).order_by(models.Rides.date.asc()).limit(5).all()
    return RideListResponse(rides=rides or [])

@app.post("/complete_ride/{ride_id}")
def complete_ride(ride_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ride = db.query(models.Rides).filter_by(id=ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.driverid != current_user.rcsid:
        raise HTTPException(status_code=403, detail="Only the driver can complete this ride")
    ride.isactive = False
    try:
        db.commit()
        db.refresh(ride)
        return RideResponse.model_validate(ride)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/cancel_ride/{ride_id}")
def cancel_ride(ride_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    ride = db.query(models.Rides).filter_by(id=ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    if ride.driverid != current_user.rcsid:
        raise HTTPException(status_code=403, detail="Only the driver can cancel this ride")
    db.delete(ride)
    try:
        db.commit()
        return {"detail": "Ride cancelled successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Pydantic model for request body
class PaymentRequest(BaseModel):
    venmo_username: str = None
    paypal_email: str = None
    accepts_cash: bool = None

@app.post("/payment")
def update_payment(payment_req: PaymentRequest, current_user: User = Depends(get_current_user)):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(rcsid=current_user.rcsid).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if payment_req.venmo_username is not None:
            user.venmo_username = payment_req.venmo_username
        if payment_req.paypal_email is not None:
            user.paypal_email = payment_req.paypal_email
        if payment_req.accepts_cash is not None:
            user.accepts_cash = payment_req.accepts_cash

        session.commit()

        return {
            "payment": {
                "venmo": user.venmo_username,
                "paypal": user.paypal_email,
                "accepts_cash": user.accepts_cash
            }
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/debug/jobs")
def debug_jobs(request: Request):
    jobs = request.app.state.scheduler.get_jobs()
    return [{"id": j.id, "next_run": str(j.next_run_time), "func": str(j.func_ref)} for j in jobs]

# Serve frontend static assets and additional pages (post.html, ride.html, etc.)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
