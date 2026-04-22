import os
import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app, get_db, get_current_user
from backend.models import Base, User

@pytest.fixture(scope="session")
def db_engine():
    database_url = os.getenv('TEST_DATABASE_URL')
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_user():
    return User(rcsid="testuser", username="The Tester", isdriver=True)
# if you want to test a rider just in the test function do mock_user.isdriver = False
@pytest.fixture(autouse=True)
def override_db(db_session, mock_user):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.clear()

client = TestClient(app)


def test_add_user():
    response = client.post("/add_user", json={"username": "Test User", "rcsid": "testuser", "isdriver": False})
    assert response.status_code == 200
    assert response.json()["username"] == "Test User"
    assert response.json()["rcsid"] == "testuser"
    assert response.json()["isdriver"] == False

def test_request_ride():
    response = client.post("/request_ride", json={"driverid": "testuser", "address": "1600 Pennsylvania Avenue NW", "origin": "456 Elm St", "cost": 10.0})
    assert response.status_code == 200
    assert response.json()["driverid"] == "testuser"
    assert response.json()["address"] == "1600 Pennsylvania Avenue NW"
    assert response.json()["origin"] == "456 Elm St"
    assert response.json()["cost"] == 10.0
    assert response.json()["lat"] == pytest.approx(38.8987, abs=0.01)
    assert response.json()["lon"] == pytest.approx(-77.0352, abs=0.01)

def test_get_upcoming_rides():
    future_date = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)).isoformat()
    create = client.post("/request_ride", json={"driverid": "testuser", "address": "1600 Pennsylvania Avenue NW", "origin": "456 Elm St", "cost": 10.0, "date": future_date})
    assert create.status_code == 200, create.json()
    ride_id = create.json()["id"]
    response = client.get("/upcoming_rides")
    assert response.status_code == 200
    assert any(r["id"] == ride_id for r in response.json()["rides"])


def test_get_ride():
    create = client.post("/request_ride", json={"driverid": "testuser", "address": "1600 Pennsylvania Avenue NW", "origin": "456 Elm St", "cost": 10.0,})
    assert create.status_code == 200
    ride_id = create.json()["id"]
    response = client.get(f"/rides/{ride_id}")
    assert response.status_code == 200
    assert response.json()["id"] == ride_id
    assert response.json()["driverid"] == "testuser"


def test_get_user():
    create = client.post("/add_user", json={"username": "The Tester", "rcsid": "testuser", "isdriver": True})
    assert create.status_code == 200
    response = client.get("/users/testuser")
    assert response.status_code == 200
    assert response.json()["rcsid"] == "testuser"
    assert response.json()["username"] == "The Tester"
    assert response.json()["isdriver"] == True

def test_complete_ride():
    create = client.post("/request_ride", json={"driverid": "testuser", "address": "1600 Pennsylvania Avenue NW", "origin": "456 Elm St", "cost": 10.0,})
    assert create.status_code == 200, create.json()
    ride_id = create.json()["id"]
    response = client.post(f"/complete_ride/{ride_id}")
    assert response.status_code == 200
    assert response.json()["id"] == ride_id
    assert response.json()["isactive"] == False

def test_cancel_ride():
    create = client.post("/request_ride", json={"driverid": "testuser", "address": "1600 Pennsylvania Avenue NW", "origin": "456 Elm St", "cost": 10.0,})
    assert create.status_code == 200, create.json()
    ride_id = create.json()["id"]
    response = client.post(f"/cancel_ride/{ride_id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Ride cancelled successfully"}

def test_cancel_ride_not_driver():
    create = client.post("/request_ride", json={"driverid": "testuser", "address": "1600 Pennsylvania Avenue NW", "origin": "456 Elm St", "cost": 10.0,})
    assert create.status_code == 200, create.json()
    ride_id = create.json()["id"]
    app.dependency_overrides[get_current_user] = lambda: User(rcsid="otheruser", username="Other User", isdriver=False)
    response = client.post(f"/cancel_ride/{ride_id}")
    assert response.status_code == 403

def test_add_rider():
    client.post("/add_user", json={"username": "The Tester", "rcsid": "testuser", "isdriver": True})
    create = client.post("/request_ride", json={"driverid": "testuser", "address": "1600 Pennsylvania Avenue NW", "origin": "456 Elm St", "cost": 10.0,})
    assert create.status_code == 200, create.json()
    ride_id = create.json()["id"]
    response = client.post(f"/rides/{ride_id}/add_rider")
    assert response.status_code == 200
    assert response.json()["id"] == ride_id
    user_response = client.get("/users/testuser")
    assert ride_id in user_response.json()["rides"]

def test_previous_rides():
    client.post("/add_user", json={"username": "The Tester", "rcsid": "testuser", "isdriver": True})
    create = client.post("/request_ride", json={"driverid": "testuser", "address": "1600 Pennsylvania Avenue NW", "origin": "456 Elm St", "cost": 10.0,})
    assert create.status_code == 200, create.json()
    ride_id = create.json()["id"]
    complete = client.post(f"/complete_ride/{ride_id}")
    assert complete.status_code == 200
    response = client.get("/previous_rides")
    assert response.status_code == 200
    assert isinstance(response.json()["rides"], list)


def test_search_rides():
    create = client.post("/request_ride", json={"driverid": "testuser", "address": "1600 Pennsylvania Avenue NW", "origin": "456 Elm St", "cost": 10.0})
    assert create.status_code == 200, create.json()
    date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S")
    response = client.get(f"/search_rides/1600 Pennsylvania Avenue NW/{date}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert response.json()[0]["ride"]["driverid"] == "testuser"
