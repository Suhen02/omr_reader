from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class College(Base):
    __tablename__ = "colleges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    batches = relationship("Batch", back_populates="college")
    students = relationship("Student", back_populates="college")

class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    college = relationship("College", back_populates="batches")
    students = relationship("Student", back_populates="batch")

class Student(Base):
    __tablename__ = "students"
    student_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    batch_id = Column(Integer, ForeignKey("batches.id"))
    meta = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    college = relationship("College", back_populates="students")
    batch = relationship("Batch", back_populates="students")
    __table_args__ = (UniqueConstraint('student_id', 'college_id', 'batch_id', name='uix_student_college_batch'),)

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    batch_id = Column(Integer, ForeignKey("batches.id"))
    raw_json = Column(Text)  # official answer key
    created_at = Column(DateTime, default=datetime.utcnow)

class FinalResult(Base):
    __tablename__ = "final_results"
    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    batch_id = Column(Integer, ForeignKey("batches.id"))
    aggregated_json = Column(Text)  # evaluated student result
    created_at = Column(DateTime, default=datetime.utcnow)
