from typing import Annotated

from fastapi import FastAPI, Depends
from sqlalchemy.orm import sessionmaker
from models import engine, User
from pydantic import BaseModel

from fastapi.security import OAuth2PasswordBearer

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# insert the data into database and start a session
Session = sessionmaker(bind=engine)
session = Session()

# Example database query to ensure models are loaded
users = session.query(User).all()

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

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}


# Working on a protected route that requires authentication
@app.get("/login")
def login(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


def decode_token(token):
    return User(
        username=token + "decoded", email="john@example.com", full_name="John Doe"
    )


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = decode_token(token)
    return user


@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user