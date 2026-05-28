import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base



DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL = "postgresql://app_user:app_password@localhost:5432/app_db"


engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()