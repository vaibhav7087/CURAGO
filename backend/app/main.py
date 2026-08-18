import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.routers import doctor, trainee, webhook, orders, vitals, analytics, sms_webhook
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from followup_scheduler import run_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the follow-up monitoring scheduler in a background thread
    print("Starting background followup scheduler...")
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    yield
    print("Shutting down...")

app = FastAPI(title="Telemedicine Phygital API V2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router, prefix="/api", tags=["Webhooks & RAG"])
app.include_router(sms_webhook.router, prefix="/api", tags=["SMS Followups"])
app.include_router(doctor.router, prefix="/api", tags=["Doctor"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(trainee.router, prefix="/api/trainee", tags=["Trainee"])
app.include_router(vitals.router, prefix="/api/tickets/vitals", tags=["Vitals"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "Telemedicine API is running!"}

@app.get("/health")
@app.get("/ping")
def health_check():
    return {"status": "ok", "service": "curago-backend"}

import os

import glob

@app.get("/download/apk")
def download_apk():
    # Provide the path to the APK
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    apk_files = glob.glob(os.path.join(static_dir, "*.apk"))
    
    if apk_files:
        # Sort by modification time to get the latest
        latest_apk = max(apk_files, key=os.path.getmtime)
        filename = os.path.basename(latest_apk)
        return FileResponse(path=latest_apk, filename=filename, media_type="application/vnd.android.package-archive")
    else:
        return {"error": "APK not yet available on server."}