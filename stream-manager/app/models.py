from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    rtmp_url = Column(String)
    stream_key = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
