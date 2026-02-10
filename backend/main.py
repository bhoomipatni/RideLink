from typing import Union

from fastapi import FastAPI
import models

app = FastAPI()
# insert the data into database and start a session
Session = sessionmaker(bind=engine)
session = Session()

# Example database query to ensure models are loaded
users = session.query(models.User).all()

# insert a user to the table during the session
# ALWAYS COMMIT WHEN YOU ARE ADDING OR EDITING DATA IN THE DATABASE OR CHANGES WILL NOT BE SAVED
new_user = models.User(username='Sandy', email='sandy@gmail.com', password='cool-password')
models.session.add(new_user)
models.session.commit()

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
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}