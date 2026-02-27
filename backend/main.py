import os
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import sessionmaker, Session
from models import engine, User as DBUser
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

app = FastAPI()

# password protection
# setup OAuth2 and point to the token endpoint for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# DB session setup
SessionLocal = sessionmaker(bind=engine)

# helper function for DB and authentication
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# helper function to get the current user based on the JWT token provided
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # decodes and verifies JWT token, extracts username from the "sub" or subject claim
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
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

# login route (when successful, returns a JWT token) used to validate user identity for protected routes
@app.post("/token", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)], db: Session = Depends(get_db)):
    # Look up user in the database
    user = db.query(DBUser).filter_by(username=form_data.username).first()

    if not user or user.password != form_data.password:
        # In production, use hashed password comparison (e.g. bcrypt) instead of plain ==
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # return a JWT token with the username as the subject claim
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

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
