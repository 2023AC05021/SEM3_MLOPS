import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./prediction_logs.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PredictionLog(Base):


    __tablename__ = "prediction_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    input_data = Column(String)
    prediction = Column(Float)


Base.metadata.create_all(bind=engine)

def log_prediction(input_data: str, prediction: float):
    db = SessionLocal()
    log_entry = PredictionLog(input_data=input_data, prediction=prediction)
    db.add(log_entry)
    db.commit()
    db.close()