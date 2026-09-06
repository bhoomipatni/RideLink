import datetime
from sqlalchemy.orm import sessionmaker
from models import engine, Rides

_Session = sessionmaker(bind=engine)

def expire_old_rides():
    db = _Session()
    try:
        now = datetime.datetime.now(datetime.timezone.utc)
        db.query(Rides).filter(
            Rides.date < now,
            Rides.isactive == True,
        ).update({"isactive": False}, synchronize_session=False)
        db.commit()
    finally:
        db.close()
