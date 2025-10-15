from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.routers import auth, inbond, material, section, exbond, duty_space, customer
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "Bhatt Iternational API",
    description = "API for Bhatt International",
    version = "1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.2.12:8000", "http://192.168.2.11:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inbond.router)
app.include_router(material.router)
app.include_router(section.router)
app.include_router(exbond.router)
app.include_router(duty_space.router)
app.include_router(customer.router)

if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)