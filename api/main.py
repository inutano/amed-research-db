"""
FastAPI application for AMED Research Database
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
from datetime import date
import sys
from pathlib import Path

# Add database module to path
sys.path.append(str(Path(__file__).parent.parent / 'database'))
from models import get_engine, get_session, Program, Institution, Researcher, Announcement, Project
from sqlalchemy import func, or_, extract

app = FastAPI(
    title="AMED Research Database API",
    description="API for accessing AMED research proposals and analytics",
    version="0.1.0"
)

# Database setup
DB_PATH = Path(__file__).parent.parent / 'database' / 'amed.db'
engine = get_engine(f'sqlite:///{DB_PATH}')

def get_db():
    session = get_session(engine)
    try:
        yield session
    finally:
        session.close()

# Response models
class ProjectResponse(BaseModel):
    id: int
    title: str
    researcher: Optional[str]
    institution: Optional[str]
    position: Optional[str]
    program: Optional[str]
    date: Optional[str]

class StatsResponse(BaseModel):
    total_projects: int
    total_researchers: int
    total_institutions: int
    total_programs: int

class InstitutionStats(BaseModel):
    name: str
    project_count: int

# Endpoints
@app.get("/")
def root():
    return {
        "message": "AMED Research Database API",
        "docs": "/docs",
        "version": "0.1.0"
    }

@app.get("/api/projects/search", response_model=List[ProjectResponse])
def search_projects(
    q: Optional[str] = Query(None, description="Search query"),
    year: Optional[int] = Query(None, description="Filter by year"),
    institution: Optional[str] = Query(None, description="Filter by institution"),
    researcher: Optional[str] = Query(None, description="Filter by researcher"),
    program: Optional[str] = Query(None, description="Filter by program"),
    limit: int = Query(20, le=100, description="Max results")
):
    """Search projects with filters"""
    session = next(get_db())
    
    query = session.query(
        Project, Researcher, Institution, Program, Announcement
    ).join(Researcher, Project.researcher_id == Researcher.id, isouter=True
    ).join(Institution, Project.institution_id == Institution.id, isouter=True
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Program, Announcement.program_id == Program.id, isouter=True)
    
    # Apply filters
    if q:
        query = query.filter(or_(
            Project.title.contains(q),
            Researcher.name.contains(q),
            Institution.name.contains(q)
        ))
    if year:
        query = query.filter(extract('year', Announcement.date) == year)
    if institution:
        query = query.filter(Institution.name.contains(institution))
    if researcher:
        query = query.filter(Researcher.name.contains(researcher))
    if program:
        query = query.filter(Program.name.contains(program))
    
    results = query.limit(limit).all()
    
    return [
        ProjectResponse(
            id=proj.id,
            title=proj.title,
            researcher=res.name if res else None,
            institution=inst.name if inst else None,
            position=proj.position,
            program=prog.name if prog else None,
            date=str(ann.date) if ann.date else None
        )
        for proj, res, inst, prog, ann in results
    ]

@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    """Get project details by ID"""
    session = next(get_db())
    
    result = session.query(
        Project, Researcher, Institution, Program, Announcement
    ).join(Researcher, Project.researcher_id == Researcher.id, isouter=True
    ).join(Institution, Project.institution_id == Institution.id, isouter=True
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Program, Announcement.program_id == Program.id, isouter=True
    ).filter(Project.id == project_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    
    proj, res, inst, prog, ann = result
    return ProjectResponse(
        id=proj.id,
        title=proj.title,
        researcher=res.name if res else None,
        institution=inst.name if inst else None,
        position=proj.position,
        program=prog.name if prog else None,
        date=str(ann.date) if ann.date else None
    )

@app.get("/api/stats/overview", response_model=StatsResponse)
def get_overview_stats():
    """Get overall statistics"""
    session = next(get_db())
    
    return StatsResponse(
        total_projects=session.query(Project).count(),
        total_researchers=session.query(Researcher).count(),
        total_institutions=session.query(Institution).count(),
        total_programs=session.query(Program).count()
    )

@app.get("/api/stats/by_institution", response_model=List[InstitutionStats])
def get_institution_stats(
    top_n: int = Query(10, le=100, description="Number of top institutions"),
    year: Optional[int] = Query(None, description="Filter by year")
):
    """Get project counts by institution"""
    session = next(get_db())
    
    query = session.query(
        Institution.name,
        func.count(Project.id).label('count')
    ).join(Project).join(Announcement)
    
    if year:
        query = query.filter(extract('year', Announcement.date) == year)
    
    results = query.group_by(Institution.name).order_by(
        func.count(Project.id).desc()
    ).limit(top_n).all()
    
    return [
        InstitutionStats(name=name, project_count=count)
        for name, count in results
    ]

@app.get("/api/stats/by_year")
def get_year_stats():
    """Get project counts by year"""
    session = next(get_db())
    
    results = session.query(
        extract('year', Announcement.date).label('year'),
        func.count(Project.id).label('count')
    ).join(Project).group_by('year').order_by('year').all()
    
    return [
        {"year": int(year), "project_count": count}
        for year, count in results if year
    ]

@app.get("/api/researchers/{name}")
def get_researcher(name: str):
    """Get researcher profile and projects"""
    session = next(get_db())
    
    researcher = session.query(Researcher).filter(
        Researcher.name.contains(name)
    ).first()
    
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
    
    projects = session.query(
        Project, Institution, Program, Announcement
    ).join(Institution, Project.institution_id == Institution.id, isouter=True
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Program, Announcement.program_id == Program.id, isouter=True
    ).filter(Project.researcher_id == researcher.id).all()
    
    return {
        "name": researcher.name,
        "project_count": len(projects),
        "projects": [
            {
                "title": proj.title,
                "institution": inst.name if inst else None,
                "program": prog.name if prog else None,
                "date": str(ann.date) if ann.date else None
            }
            for proj, inst, prog, ann in projects
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
