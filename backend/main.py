from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import sessionmaker, Session
from models import engine, User as DBUser
from pydantic import BaseModel

app = FastAPI()

# setup OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# DB session setup
SessionLocal = sessionmaker(bind=engine)

# helper function for DB and authentication
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    user = db.query(DBUser).filter_by(username=token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

# Pydantic models for request/response validation
class RideRequest(BaseModel):
    driverid: int
    address: str
    cost: float
    description: str | None = None
    lat: float
    long: float

# this model inputs user data for registration
class UserIn(BaseModel):
    username: str
    email: str
    rcsid: str
    isdriver: bool
    password: str

# this model will output user data for login (EXCLUDES PASSWORD)
class UserOut(BaseModel):
    username: str
    email: str | None = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str

# login route
@app.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    # Look up user in the database
    user = db.query(DBUser).filter_by(username=form_data.username).first()

    if not user or user.password != form_data.password:
        # In production, use hashed password comparison (e.g. bcrypt) instead of plain ==
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # In production, return a signed JWT here instead of just the username
    return {"access_token": user.username, "token_type": "bearer"}

# protected/authenticated route example
@app.get("/users/me", response_model=UserOut)
def read_users_me(current_user: Annotated[DBUser, Depends(get_current_user)]):
    return current_user

# registration route
@app.post("/register", response_model=UserOut)
def register(user: UserIn, db: Session = Depends(get_db)):
    
    if db.query(DBUser).filter_by(username=user.username).first():
        raise HTTPException(status_code=400, detail= "Username already exists! Try again.")
    
    if db.query(DBUser).filter_by(email=user.email).first():
        raise HTTPException(status_code=400, detail= "There is already an account registered to this email! Try again.")
    
    new_user = DBUser(
        username=user.username,
        email=user.email,
        password=user.password,
        rcsid=user.rcsid
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
