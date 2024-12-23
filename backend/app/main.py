from fastapi import FastAPI
from routers import payments, evidence

app = FastAPI(title="Payment Management API")

# Include Routers
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Payment Management API"}
