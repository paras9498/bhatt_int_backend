from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.routers import auth, inbond, material, section, exbond, duty_space, customer, dispatch
from app.database import engine, Base,SessionLocal
from app.models.auth_model import User
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

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
    allow_origins=["http://192.168.2.12:8000", "http://192.168.2.2:3000", "http://localhost:3000", "https://bhattinternational.vercel.app"],
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
app.include_router(dispatch.router)

# ---------- Create static admin user on startup ----------
def create_admin_user():
    db = SessionLocal()
    try:
        admin_email = "admin1@gmail.com"
        password="admin123"
        hashed_password = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            admin = User(
                username="admin",
                email=admin_email,
                password=hashed_password,  # ⚠️ Hash this in production
            )
            db.add(admin)
            db.commit()
        else:
            print("ℹ️ Admin user already exists.")
    except IntegrityError:
        db.rollback()
        print("⚠️ Failed to insert admin user due to IntegrityError.")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    create_admin_user()

if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)