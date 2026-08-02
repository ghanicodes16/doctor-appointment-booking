"""
main.py - Entry point of the FastAPI backend.

This file creates the FastAPI application, registers the routers and
enables CORS so the React frontend (which runs on a different port)
can talk to the API.

Run the server with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import appointments, auth, doctors, notifications, patients, reviews, search
from .seed import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts.

    We use it to create tables and insert the demo data, so the app is
    ready to use as soon as uvicorn starts.
    """
    seed_data()
    yield


# Create the FastAPI application.
app = FastAPI(
    title="Doctor Appointment Booking System",
    description="A full-stack doctor appointment booking API with patient and doctor portals.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS (Cross-Origin Resource Sharing).
# The React dev server runs on http://localhost:5173, which is a
# different "origin" than the API on http://localhost:8000. CORS tells
# the browser it is allowed to call our API from that origin.
# For this academic project we allow all origins; in production you
# would restrict this to your own domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the API routers. Each router handles a group of endpoints.
app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(search.router)
app.include_router(reviews.router)
app.include_router(notifications.router)


@app.get("/")
def root():
    """Simple welcome message at the API root."""
    return {"message": "Welcome to the Doctor Appointment Booking API. Visit /docs for documentation."}
