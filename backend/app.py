import os
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.metadata import OneLogin_Saml2_Metadata
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.orm import sessionmaker
from .models import engine, User, Rides, RideRequest

# Load environment variables from backend/.env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

SECRET_KEY = os.environ.get("SESSION_SECRET") or os.environ.get("SESSION_SECRET")
if not SECRET_KEY:
    raise RuntimeError("SESSION_SECRET environment variable is not set. Please configure it in backend/.env")
serializer = URLSafeTimedSerializer(SECRET_KEY)

app = FastAPI()

# Enable CORS for SAML callback from IdP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set base directory for file paths
base_dir = Path(__file__).parent

# Load settings.json
with open(base_dir / "config" / "settings.json") as f:
    settings = json.load(f)

# Keep SAML callback URLs aligned with the environment where the app runs.
app_base_url = os.getenv(
    "APP_BASE_URL", "https://ridelink.cs.rpi.edu:8000"
).rstrip("/")
settings["sp"]["entityId"] = f"{app_base_url}/metadata"
settings["sp"]["assertionConsumerService"]["url"] = f"{app_base_url}/callback"
FRONTEND_HOME = "/"

# Inject private key from .env
settings["sp"]["privateKey"] = os.environ["SAML_PRIVATE_KEY"].replace("\\n", "\n")


# Load x509cert
with open(base_dir / "keys" / "server.crt") as f:
    settings["sp"]["x509cert"] = f.read()

# Initialize SAML auth (helper)
def init_saml_auth(req):
    return OneLogin_Saml2_Auth(req, settings)


def validate_sp_metadata(metadata_xml: str):
    """Handle python3-saml validator naming differences across versions."""
    if hasattr(OneLogin_Saml2_Metadata, "validate_metadata"):
        return OneLogin_Saml2_Metadata.validate_metadata(metadata_xml)
    if hasattr(OneLogin_Saml2_Metadata, "validateMetadata"):
        return OneLogin_Saml2_Metadata.validateMetadata(metadata_xml)
    return []

# Helper to convert FastAPI request to what python3-saml expects
async def prepare_flask_request(request: Request):
    # Determine the correct default port based on scheme
    default_port = 443 if request.url.scheme == 'https' else 80
    port = request.url.port or default_port
    
    # For POST requests, try to get form data
    post_data = {}
    if request.method == 'POST':
        try:
            post_data = dict(await request.form())
        except Exception as e:
            print(f"Error reading POST data: {e}")
    
    return {
        'http_host': request.url.hostname,
        'script_name': str(request.url.path),
        'server_port': port,
        'get_data': dict(request.query_params),
        'post_data': post_data,
        'https': 'on' if request.url.scheme == 'https' else 'off'
    }


# Database session
_Session = sessionmaker(bind=engine)

def get_session():
    return _Session()

# Database helper functions
def get_user_by_id(user_id):
    db = get_session()
    try:
        return db.query(User).filter(User.rcsid == user_id).first()
    finally:
        db.close()

def get_or_create_user(netid, email, first_name, last_name):
    db = get_session()
    try:
        user = db.query(User).filter(User.rcsid == netid).first()
        if not user:
            user = User(
                rcsid=netid,
                username=netid.split("@")[0] if "@" in netid else netid,
                isdriver=False
            )
            db.add(user)
            db.commit()
        return user
    finally:
        db.close()


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse(base_dir / ".." / "frontend" / "index.html")

@app.get("/login")
async def login(request: Request):
    req = await prepare_flask_request(request)
    auth = init_saml_auth(req)
    # Redirect the browser directly to the identity provider login.
    return RedirectResponse(url=auth.login())


@app.post("/callback")
async def callback(request: Request):
    req = await prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()

    if errors:
        return RedirectResponse(url="https://your-frontend-domain.com/login?error=saml")

    name_id = auth.get_nameid()          # e.g. netid@rpi.edu
    attrs = auth.get_attributes()

    # pull whatever RPI's IdP actually sends — check attrs.keys() by logging once
    email = attrs.get("email", [None])[0] or name_id
    first_name = attrs.get("givenName", [""])[0]
    last_name = attrs.get("sn", [""])[0]

    user = get_or_create_user(netid=name_id, email=email,
                               first_name=first_name, last_name=last_name)

    session_token = serializer.dumps({"user_id": user.rcsid, "netid": name_id})

    response = RedirectResponse(url=FRONTEND_HOME, status_code=302)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        max_age=60 * 60 * 8,
    )
    return response
@app.get("/metadata", response_class=HTMLResponse)
def metadata():
    metadata = OneLogin_Saml2_Metadata.builder(settings["sp"], None, True)
    errors = validate_sp_metadata(metadata)
    if len(errors) > 0:
        return {"errors": errors}
    return HTMLResponse(content=metadata, media_type="text/xml")


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("session")
    return response

@app.get("/me")
def me(request: Request):
    token = request.cookies.get("session")
    if not token:
        return {"authenticated": False}
    try:
        data = serializer.loads(token, max_age=60 * 60 * 8)
    except Exception:
        return {"authenticated": False}
    user = get_user_by_id(data["user_id"])
    return {"authenticated": True, "user": user.to_dict() if user else None}


@app.get("/google-maps-config")
def google_maps_config():
    """Return the browser-restricted Maps key used by the post-trip page."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Google Maps is not configured")
    return {"api_key": api_key}


@app.get("/my_trips")
def my_trips(request: Request):
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id = serializer.loads(token, max_age=60 * 60 * 8)["netid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")

    db = get_session()
    try:
        now = datetime.now(timezone.utc)
        driver_rides = db.query(Rides).filter(Rides.driverid == user_id).all()
        requests = db.query(RideRequest).filter(
            RideRequest.rider_rcsid == user_id
        ).all()
        driver_requests = db.query(RideRequest).all()

        def trip_data(ride, status, role, request_records):
            ride_date = ride.date
            if ride_date.tzinfo is None:
                ride_date = ride_date.replace(tzinfo=timezone.utc)
            driver = db.query(User).filter(User.rcsid == ride.driverid).first()
            accepted_passengers = []
            for item in request_records:
                if item.ride_id == ride.id and item.status == "accepted":
                    passenger = db.query(User).filter(
                        User.rcsid == item.rider_rcsid
                    ).first()
                    if passenger:
                        accepted_passengers.append({
                            "name": passenger.username,
                            "id": passenger.rcsid,
                            "status": "confirmed",
                            "payment_status": "unpaid",
                        })
            return {
                "id": ride.id,
                "origin": ride.origin,
                "destination": ride.address,
                "date": ride_date.isoformat(),
                "day": ride_date.strftime("%A"),
                "time": ride_date.strftime("%I:%M %p").lstrip("0"),
                "cost": ride.cost,
                "distance": "N/A",
                "status": status,
                "role": role,
                "driver": driver.username if driver else ride.driverid,
                "seats_total": ride.seat_count,
                "passengers": accepted_passengers,
                "seats_filled": sum(
                    1 for item in request_records
                    if item.ride_id == ride.id and item.status == "accepted"
                ),
            }

        driver = [
            trip_data(
                ride,
                "active" if ride.isactive else "completed",
                "driver",
                driver_requests,
            )
            for ride in driver_rides
        ]
        rider = [
            trip_data(request_ride, request.status, "rider", requests)
            for request in requests
            for request_ride in db.query(Rides).filter(Rides.id == request.ride_id).all()
        ]
        return {
            "upcoming": [item for item in rider if datetime.fromisoformat(item["date"]) >= now],
            "past": [item for item in rider if datetime.fromisoformat(item["date"]) < now],
            "driver": driver,
        }
    finally:
        db.close()


# --- Ride Endpoints ---

@app.post("/request_ride")
async def request_ride(request: Request):
    """Driver creates a new ride post."""
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        data = serializer.loads(token, max_age=60 * 60 * 8)
        driver_rcsid = data.get("netid")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    body = await request.json()
    
    # Extract form data
    origin = body.get("origin")
    address = body.get("address")
    date = body.get("date")
    cost = body.get("cost", 10.50)
    seat_count = body.get("seats", 4)
    description = body.get("description", "")
    
    if not origin or not address or not date:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    db = get_session()
    try:
        # Placeholder coordinates (in production, geocode the address)
        ride = Rides(
            driverid=driver_rcsid,
            origin=origin,
            address=address,
            date=date,
            cost=cost,
            seat_count=seat_count,
            description=description,
            lat=40.7128,  # Default to NYC; replace with geocoding
            lon=-74.0060,
            riders=[]
        )
        db.add(ride)
        db.commit()
        return {"id": ride.id, "status": "created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@app.get("/search_rides/{destination}/{date}")
async def search_rides(destination: str, date: str):
    """Search for available rides by destination and date."""
    db = get_session()
    try:
        # Simple substring search on address/origin
        from datetime import datetime, timezone
        search_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        rides = db.query(Rides).filter(
            Rides.isactive == True,
            Rides.address.ilike(f"%{destination}%") | Rides.origin.ilike(f"%{destination}%"),
            Rides.date >= search_date,
            Rides.date < search_date.replace(hour=23, minute=59, second=59)
        ).all()
        return [{"ride": r.to_dict(), "detour_eta": None, "true_eta": None} for r in rides]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@app.post("/add_rider")
async def add_rider(request: Request):
    """Rider requests to join a ride."""
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        data = serializer.loads(token, max_age=60 * 60 * 8)
        rider_rcsid = data.get("netid")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    body = await request.json()
    ride_id = body.get("ride_id")
    
    if not ride_id:
        raise HTTPException(status_code=400, detail="Missing ride_id")
    
    db = get_session()
    try:
        ride = db.query(Rides).filter(Rides.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        # Add rider to the riders list
        ride_request = db.query(RideRequest).filter(
            RideRequest.ride_id == ride_id,
            RideRequest.rider_rcsid == rider_rcsid,
        ).first()
        if ride_request is None:
            ride_request = RideRequest(
                ride_id=ride_id,
                rider_rcsid=rider_rcsid,
                status="pending",
            )
            db.add(ride_request)
        elif ride_request.status != "accepted":
            ride_request.status = "pending"
        
        db.commit()
        return {"status": ride_request.status, "ride_id": ride_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@app.post("/accept_rider/{ride_id}/{rider_rcsid}")
async def accept_rider(request: Request, ride_id: int, rider_rcsid: str):
    """Driver accepts a rider's request."""
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        data = serializer.loads(token, max_age=60 * 60 * 8)
        driver_rcsid = data.get("netid")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    db = get_session()
    try:
        ride = db.query(Rides).filter(Rides.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        if ride.driverid != driver_rcsid:
            raise HTTPException(status_code=403, detail="Not the driver of this ride")
        
        ride_request = db.query(RideRequest).filter(
            RideRequest.ride_id == ride_id,
            RideRequest.rider_rcsid == rider_rcsid,
        ).first()
        if not ride_request:
            raise HTTPException(status_code=404, detail="Ride request not found")
        ride_request.status = "accepted"
        db.commit()
        return {"status": "accepted", "rider": rider_rcsid}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@app.post("/deny_rider/{ride_id}/{rider_rcsid}")
async def deny_rider(request: Request, ride_id: int, rider_rcsid: str):
    """Driver denies a rider's request."""
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        data = serializer.loads(token, max_age=60 * 60 * 8)
        driver_rcsid = data.get("netid")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    db = get_session()
    try:
        ride = db.query(Rides).filter(Rides.id == ride_id).first()
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        if ride.driverid != driver_rcsid:
            raise HTTPException(status_code=403, detail="Not the driver of this ride")
        
        ride_request = db.query(RideRequest).filter(
            RideRequest.ride_id == ride_id,
            RideRequest.rider_rcsid == rider_rcsid,
        ).first()
        if not ride_request:
            raise HTTPException(status_code=404, detail="Ride request not found")
        ride_request.status = "denied"
        
        db.commit()
        return {"status": "denied", "rider": rider_rcsid}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()
    return {"authenticated": True, "user": user.to_dict()}


# Serve the static frontend after API routes so page assets and HTML files share
# the same origin as the backend API.
app.mount(
    "/",
    StaticFiles(directory=base_dir.parent / "frontend", html=True),
    name="frontend",
)

