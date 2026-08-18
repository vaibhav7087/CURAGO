from fastapi import FastAPI
from app.routers import doctor, trainee, webhook, orders, vitals, analytics, sms_webhook
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Telemedicine Phygital API V2")

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