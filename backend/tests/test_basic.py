from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# TODO: SETUP FIXTURE FOR DATABASE FOR TESTING

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}

def test_add_user():
    response = client.post("/add_user", json={"rcsid": "testuser", "isdriver": False})
    assert response.status_code == 200
    assert response.json() == {"rcsid": "testuser", "isdriver": False, "rides": None, "payment_methods": None}

def test_add_ride():
    response = client.post("/add_ride", json={"driverid": "testuser", "address": "123 Main St", "orgin": "456 Elm St", "cost": 10.0, "lat": 40.7128, "lon": -74.0060})
    assert response.status_code == 200
    assert response.json()["driverid"] == "testuser"
    assert response.json()["address"] == "123 Main St"
    assert response.json()["orgin"] == "456 Elm St"
    assert response.json()["cost"] == 10.0
    assert response.json()["lat"] == 40.7128
    assert response.json()["lon"] == -74.0060