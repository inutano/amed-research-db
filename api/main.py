"""
FastAPI application for AMED Research Database
"""
from fastapi import FastAPI, Query, HTTPException, Request
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
    description="API for accessing AMED research proposals and analytics. Designed for LLM and AI agent consumption.",
    version="0.3.0"
)

# Register analytics router
from api.analytics import router as analytics_router
app.include_router(analytics_router)

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

# Helpers

def _compact_project(proj_resp):
    """Convert a full project response to compact format."""
    parts = []
    if proj_resp.get("researcher"):
        parts.append(proj_resp["researcher"])
    if proj_resp.get("institution"):
        parts.append(proj_resp["institution"])
    return {
        "id": proj_resp["id"],
        "title": proj_resp["title"],
        "by": " / ".join(parts) if parts else None,
        "program": proj_resp.get("program"),
        "date": proj_resp.get("date"),
    }

# Endpoints
@app.get("/")
def root():
    return {
        "message": "AMED Research Database API",
        "docs": "/docs",
        "version": "0.1.0"
    }

@app.get("/api/projects/search")
def search_projects(
    q: Optional[str] = Query(None, description="Search query"),
    year: Optional[int] = Query(None, description="Filter by year"),
    institution: Optional[str] = Query(None, description="Filter by institution"),
    researcher: Optional[str] = Query(None, description="Filter by researcher"),
    program: Optional[str] = Query(None, description="Filter by program"),
    limit: int = Query(20, le=100, description="Max results"),
    format: Optional[str] = Query(None, description="Response format: 'compact' for condensed output"),
):
    """Search projects with filters. Use format=compact for LLM-optimized condensed output."""
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

    total = query.count()
    results = query.limit(limit).all()

    projects = [
        {
            "id": proj.id,
            "title": proj.title,
            "researcher": res.name if res else None,
            "institution": inst.name if inst else None,
            "position": proj.position,
            "program": prog.name if prog else None,
            "date": str(ann.date) if ann.date else None,
        }
        for proj, res, inst, prog, ann in results
    ]

    if format == "compact":
        projects = [_compact_project(p) for p in projects]

    return {
        "total": total,
        "returned": len(projects),
        "projects": projects,
    }

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

# --- Quick Win 1: Metadata Endpoint ---

@app.get("/api/metadata")
def get_metadata():
    """Return schema info, available filters, and value ranges for LLM query planning."""
    session = next(get_db())

    years = [
        int(y) for (y,) in session.query(
            extract('year', Announcement.date)
        ).distinct().order_by(extract('year', Announcement.date)).all()
        if y
    ]

    top_programs = [
        name for (name,) in session.query(Program.name).join(Announcement).join(Project).group_by(
            Program.name
        ).order_by(func.count(Project.id).desc()).limit(20).all()
    ]

    top_institutions = [
        name for (name,) in session.query(Institution.name).join(Project).group_by(
            Institution.name
        ).order_by(func.count(Project.id).desc()).limit(20).all()
    ]

    return {
        "database": {
            "total_projects": session.query(Project).count(),
            "total_researchers": session.query(Researcher).count(),
            "total_institutions": session.query(Institution).count(),
            "total_programs": session.query(Program).count(),
            "total_announcements": session.query(Announcement).count(),
        },
        "filters": {
            "years": years,
            "top_programs": top_programs,
            "top_institutions": top_institutions,
        },
        "endpoints": [
            {"method": "GET", "path": "/api/projects/search", "params": ["q", "year", "institution", "researcher", "program", "limit", "format"]},
            {"method": "GET", "path": "/api/projects/{id}", "params": ["format"]},
            {"method": "GET", "path": "/api/stats/overview"},
            {"method": "GET", "path": "/api/stats/by_institution", "params": ["top_n", "year"]},
            {"method": "GET", "path": "/api/stats/by_year"},
            {"method": "GET", "path": "/api/researchers/{name}"},
            {"method": "GET", "path": "/api/analytics/trends/programs", "params": ["program", "top_n"]},
            {"method": "GET", "path": "/api/analytics/trends/institutions", "params": ["institution", "top_n"]},
            {"method": "GET", "path": "/api/analytics/compare", "params": ["institutions", "programs"]},
            {"method": "GET", "path": "/api/analytics/programs/{name}"},
            {"method": "GET", "path": "/api/analytics/institutions/{name}"},
            {"method": "GET", "path": "/api/analytics/young_researchers", "params": ["year", "top_n"]},
            {"method": "GET", "path": "/api/analytics/keyword_search", "params": ["keywords"]},
            {"method": "GET", "path": "/api/analytics/collaborations", "params": ["institution", "program", "top_n"]},
            {"method": "GET", "path": "/api/metadata"},
            {"method": "GET", "path": "/api/suggestions"},
            {"method": "POST", "path": "/api/bulk", "body": {"queries": [{"path": "...", "params": {}}]}},
        ],
        "format_options": ["full (default)", "compact"],
    }


# --- Quick Win 2: Query Suggestions Endpoint ---

@app.get("/api/suggestions")
def get_suggestions():
    """Return example queries to help LLMs understand API capabilities."""
    return {
        "description": "Example queries for the AMED Research Database API",
        "examples": [
            {
                "intent": "Search for cancer research projects",
                "url": "/api/projects/search?q=がん&limit=10",
            },
            {
                "intent": "Search projects by institution",
                "url": "/api/projects/search?institution=東京大学&limit=10",
            },
            {
                "intent": "Get projects from a specific year",
                "url": "/api/projects/search?year=2025&limit=20",
            },
            {
                "intent": "Search by researcher name",
                "url": "/api/projects/search?researcher=田中&limit=10",
            },
            {
                "intent": "Search by program name",
                "url": "/api/projects/search?program=がん医療&limit=10",
            },
            {
                "intent": "Combine filters",
                "url": "/api/projects/search?q=AI&year=2025&institution=大学&limit=10",
            },
            {
                "intent": "Get compact results for large queries",
                "url": "/api/projects/search?q=感染症&limit=50&format=compact",
            },
            {
                "intent": "Top institutions overall",
                "url": "/api/stats/by_institution?top_n=10",
            },
            {
                "intent": "Top institutions in a specific year",
                "url": "/api/stats/by_institution?top_n=10&year=2025",
            },
            {
                "intent": "Project counts by year",
                "url": "/api/stats/by_year",
            },
            {
                "intent": "Overall database statistics",
                "url": "/api/stats/overview",
            },
            {
                "intent": "Researcher profile",
                "url": "/api/researchers/山田",
            },
            {
                "intent": "Program trends over years",
                "url": "/api/analytics/trends/programs?top_n=5",
            },
            {
                "intent": "Institution trends over years",
                "url": "/api/analytics/trends/institutions?institution=大学&top_n=5",
            },
            {
                "intent": "Compare two institutions",
                "url": "/api/analytics/compare?institutions=東京大学,京都大学",
            },
            {
                "intent": "Detailed program analytics",
                "url": "/api/analytics/programs/がん医療",
            },
            {
                "intent": "Detailed institution analytics",
                "url": "/api/analytics/institutions/東京大学",
            },
            {
                "intent": "Young researcher statistics",
                "url": "/api/analytics/young_researchers",
            },
            {
                "intent": "Keyword frequency analysis over time",
                "url": "/api/analytics/keyword_search?keywords=AI,ゲノム,がん",
            },
            {
                "intent": "Find collaborating institutions",
                "url": "/api/analytics/collaborations?institution=東京大学",
            },
            {
                "intent": "Run multiple queries at once",
                "method": "POST",
                "url": "/api/bulk",
                "body": {
                    "queries": [
                        {"path": "/api/stats/overview"},
                        {"path": "/api/stats/by_institution", "params": {"top_n": 5}},
                        {"path": "/api/projects/search", "params": {"q": "がん", "limit": 5, "format": "compact"}},
                    ]
                },
            },
        ],
    }


# --- Quick Win 3: Bulk Query Endpoint ---

class BulkQueryItem(BaseModel):
    path: str
    params: Optional[dict] = None

class BulkRequest(BaseModel):
    queries: List[BulkQueryItem]

@app.post("/api/bulk")
async def bulk_query(request: BulkRequest, raw_request: Request):
    """Execute multiple API queries in a single request. Max 10 queries."""
    if len(request.queries) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 queries per bulk request")

    results = []
    for q in request.queries:
        # Build internal URL with params
        url = q.path
        if q.params:
            param_str = "&".join(f"{k}={v}" for k, v in q.params.items())
            url = f"{q.path}?{param_str}"

        # Use the test client to call internal routes
        from starlette.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(url)
        results.append({
            "path": q.path,
            "status": resp.status_code,
            "data": resp.json() if resp.status_code == 200 else {"error": resp.text},
        })

    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
