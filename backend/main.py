from typing import Union

from fastapi import FastAPI
from backend import models

app = FastAPI()

# Example database query to ensure models are loaded
users = models.session.query(models.User).all()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"result": item_id,}