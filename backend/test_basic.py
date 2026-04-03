import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from backend.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base

client = TestClient(app)

@pytest.fixture(scope="session")
def db_engine():
    database_url = os.getenv('DATABASE_URL')
    engine = create_engine(database_url)
    # Create all tables defined in Base.metadata
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    # Bind a session to the connection
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}

def test_add_user(db_session):
    response = client.post("/add_user", json={"username": "Test User", "rcsid": "testuser", "isdriver": False})
    assert response.status_code == 200
    assert response.json() == {"username": "Test User", "rcsid": "testuser", "isdriver": False}

def test_request_ride(db_session):
    response = client.post("/request_ride", json={"driverid": "testuser", "address": "123 Main St", "origin": "456 Elm St", "cost": 10.0, "lat": 40.7128, "lon": -74.0060})
    assert response.status_code == 200
    assert response.json()["driverid"] == "testuser"
    assert response.json()["address"] == "123 Main St"
    assert response.json()["origin"] == "456 Elm St"
    assert response.json()["cost"] == 10.0
    assert response.json()["lat"] == 40.7128
    assert response.json()["lon"] == -74.0060

def test_get_upcoming_rides(db_session):
    response = client.get("/upcoming_rides")
    assert response.status_code == 200
    assert isinstance(response.json(), list)