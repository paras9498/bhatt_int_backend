from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# MYSQL_HOST = os.getenv("MYSQL_HOST")
# MYSQL_USER = os.getenv("MYSQL_USER")
# MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
# MYSQL_DB = os.getenv("MYSQL_DB")


MYSQL_HOST = "3mo1j3.h.filess.io:3306"
MYSQL_USER = "igt_database_rapidlyten"
MYSQL_PASSWORD = "fa131fc31843c2542d2fc4c8bd49ebbd0eac77bc"
MYSQL_DB = "igt_database_rapidlyten"

# Connection URL using mysqlconnector
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()