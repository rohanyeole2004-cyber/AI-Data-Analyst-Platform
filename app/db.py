from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
Base = declarative_base()
class Dataset(Base):
    __tablename__ = 'datasets'
    id=Column(Integer,primary_key=True)
    filename=Column(String(255),nullable=False)
    storage_path=Column(String(500))
    rows=Column(Integer)
    columns=Column(Integer)
    created_at=Column(DateTime,default=datetime.utcnow)
engine=create_engine(settings.database_url,connect_args={'check_same_thread':False} if settings.database_url.startswith('sqlite') else {})
SessionLocal=sessionmaker(bind=engine)
def init_db(): Base.metadata.create_all(engine)
