"""
Database models for AMED research projects
"""
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Program(Base):
    __tablename__ = 'programs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(500), unique=True, nullable=False, index=True)
    announcements = relationship('Announcement', back_populates='program')

class Institution(Base):
    __tablename__ = 'institutions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    projects = relationship('Project', back_populates='institution')

class Researcher(Base):
    __tablename__ = 'researchers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    projects = relationship('Project', back_populates='researcher')

class Announcement(Base):
    __tablename__ = 'announcements'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False)
    page_title = Column(String(500))
    program_id = Column(Integer, ForeignKey('programs.id'))
    date = Column(Date, index=True)
    young_researcher_flag = Column(Boolean, default=False)
    
    program = relationship('Program', back_populates='announcements')
    projects = relationship('Project', back_populates='announcement')

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    announcement_id = Column(Integer, ForeignKey('announcements.id'), nullable=False)
    title = Column(Text, nullable=False)
    researcher_id = Column(Integer, ForeignKey('researchers.id'))
    institution_id = Column(Integer, ForeignKey('institutions.id'))
    position = Column(String(100))
    
    announcement = relationship('Announcement', back_populates='projects')
    researcher = relationship('Researcher', back_populates='projects')
    institution = relationship('Institution', back_populates='projects')

def get_engine(db_path='sqlite:///amed.db'):
    return create_engine(db_path, echo=False)

def init_db(db_path='sqlite:///amed.db'):
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
