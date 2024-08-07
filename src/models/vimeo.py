from src.orm import db
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class Vimeo(db.Model):
    __tablename__ = 'vimeo_account'
    

    """ Primary Key """
    id = Column(Integer, primary_key=True)

    """ Foreign Keys """
    package_user_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))

    """ Housekeeping """
    datetime_created = Column(DateTime, default=datetime.utcnow)
    
    "google email account"
    vimeo_email = Column(String(255), index=True, unique=True)
    
    "google access token"
    access_token = Column(String(255), index=True)
    
    "google refresh token"
    refresh_token = Column(String(255), index=True)
    
    """ Relationships"""
    user = relationship("User",back_populates="vimeos")

    def to_json(self):
        response_json = {c.name: getattr(self, c.name)
                         for c in self.__table__.columns}
        return response_json