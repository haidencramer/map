from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import Field, Session, SQLModel, create_engine, select
import os

# --- DATABASE SETUP ---
# Default to local "map_data.db" for laptop testing, but allow the server to override it
db_path = os.getenv("DB_PATH", "map_data.db")
sqlite_url = f"sqlite:///{db_path}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


# Define our Database Table
class LocationPin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    comment: str
    lat: float
    lng: float

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

# Database session dependency
def get_session():
    with Session(engine) as session:
        yield session

# --- ROUTES ---

@app.get("/")
def serve_frontend():
    # Serve the HTML file directly
    with open("index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api/pins", response_model=list[LocationPin])
def get_pins(session: Session = Depends(get_session)):
    # Fetch all pins from the database
    pins = session.exec(select(LocationPin)).all()
    return pins

@app.post("/api/pins", response_model=LocationPin)
def create_pin(pin: LocationPin, session: Session = Depends(get_session)):
    # Save a new pin to the database
    session.add(pin)
    session.commit()
    session.refresh(pin)
    return pin