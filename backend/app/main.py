from fastapi import FastAPI
from app.routers import doctor, trainee, webhook, orders
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
app.include_router(doctor.router, prefix="/api", tags=["Doctor"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(trainee.router, prefix="/api/trainee", tags=["Trainee"])

@app.get("/")
def root():
    return {"message": "Telemedicine API is running!"}