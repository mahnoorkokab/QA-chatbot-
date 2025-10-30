from sqlalchemy import Column, Integer, String, Text
from database import Base
from pydantic import BaseModel, EmailStr

# -----------------------------
# SQLAlchemy Models
# -----------------------------
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    content = Column(Text)
    pinecone_id = Column(String)

# -----------------------------
# Pydantic Models
# -----------------------------
class User(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    username: str
    msg: str

class DocumentUpdate(BaseModel):
    filename: str | None = None
    content: str | None = None
