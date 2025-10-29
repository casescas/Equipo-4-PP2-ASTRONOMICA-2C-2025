from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tensorflow.keras.models import load_model
from apscheduler.schedulers.background import BackgroundScheduler
from config.db_init import init_database
import uvicorn
from jobs.scheduler import (
    start_scheduler,
    stop_scheduler,
)
from routers import cloud_routes, images_routes, weather_routes

app = FastAPI()
scheduler = BackgroundScheduler()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    print("INFO: Iniciando servidor FastAPI...")
    init_database()

    print("INFO: Iniciando scheduler...")
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()


app.include_router(cloud_routes.router)
app.include_router(weather_routes.router)
app.include_router(images_routes.router)


@app.get("/")
def home():
    return {"mensaje": "Servidor de nubosidad Río Grande activo 🚀"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
