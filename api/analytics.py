"""
Analytics endpoints for AMED Research Database
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from sqlalchemy import func, extract, and_, case
from collections import defaultdict

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'database'))
from models import Program, Institution, Researcher, Announcement, Project

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/trends/programs")
def program_trends(
    program: Optional[str] = Query(None, description="Filter by program name (partial match)"),
    top_n: int = Query(10, le=50, description="Number of top programs to show"),
):
    """Show how programs have grown or shrunk over the years."""
    from api.main import get_db
    session = next(get_db())

    query = session.query(
        Program.name,
        extract('year', Announcement.date).label('year'),
        func.count(Project.id).label('count'),
    ).join(Announcement, Program.id == Announcement.program_id
    ).join(Project, Announcement.id == Project.announcement_id
    ).filter(Announcement.date.isnot(None))

    if program:
        query = query.filter(Program.name.contains(program))

    rows = query.group_by(Program.name, 'year').order_by(Program.name, 'year').all()

    # Build per-program time series
    programs = defaultdict(lambda: {"years": {}, "total": 0})
    for name, year, count in rows:
        y = int(year)
        programs[name]["years"][y] = count
        programs[name]["total"] += count

    # Sort by total and limit
    sorted_programs = sorted(programs.items(), key=lambda x: x[1]["total"], reverse=True)[:top_n]

    return {
        "programs": [
            {
                "name": name,
                "total": data["total"],
                "by_year": dict(sorted(data["years"].items())),
            }
            for name, data in sorted_programs
        ]
    }


@router.get("/trends/institutions")
def institution_trends(
    institution: Optional[str] = Query(None, description="Filter by institution name (partial match)"),
    top_n: int = Query(10, le=50, description="Number of top institutions to show"),
):
    """Show how institutions' project counts have changed over the years."""
    from api.main import get_db
    session = next(get_db())

    query = session.query(
        Institution.name,
        extract('year', Announcement.date).label('year'),
        func.count(Project.id).label('count'),
    ).join(Project, Institution.id == Project.institution_id
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).filter(Announcement.date.isnot(None))

    if institution:
        query = query.filter(Institution.name.contains(institution))

    rows = query.group_by(Institution.name, 'year').order_by(Institution.name, 'year').all()

    institutions = defaultdict(lambda: {"years": {}, "total": 0})
    for name, year, count in rows:
        y = int(year)
        institutions[name]["years"][y] = count
        institutions[name]["total"] += count

    sorted_inst = sorted(institutions.items(), key=lambda x: x[1]["total"], reverse=True)[:top_n]

    return {
        "institutions": [
            {
                "name": name,
                "total": data["total"],
                "by_year": dict(sorted(data["years"].items())),
            }
            for name, data in sorted_inst
        ]
    }


@router.get("/compare")
def compare_entities(
    institutions: Optional[str] = Query(None, description="Comma-separated institution names to compare"),
    programs: Optional[str] = Query(None, description="Comma-separated program names to compare"),
):
    """Compare institutions or programs side by side across years."""
    from api.main import get_db
    session = next(get_db())

    if not institutions and not programs:
        raise HTTPException(status_code=400, detail="Provide 'institutions' or 'programs' parameter (comma-separated)")

    if institutions:
        names = [n.strip() for n in institutions.split(",")]
        results = {}
        for name in names:
            rows = session.query(
                extract('year', Announcement.date).label('year'),
                func.count(Project.id).label('count'),
            ).select_from(Project
            ).join(Announcement, Project.announcement_id == Announcement.id
            ).join(Institution, Project.institution_id == Institution.id
            ).filter(Institution.name.contains(name), Announcement.date.isnot(None)
            ).group_by('year').order_by('year').all()

            total = sum(c for _, c in rows)
            by_year = {int(y): c for y, c in rows}

            # Top programs for this institution
            top_progs = session.query(
                Program.name, func.count(Project.id).label('count'),
            ).select_from(Project
            ).join(Announcement, Project.announcement_id == Announcement.id
            ).join(Program, Announcement.program_id == Program.id
            ).join(Institution, Project.institution_id == Institution.id
            ).filter(Institution.name.contains(name)
            ).group_by(Program.name).order_by(func.count(Project.id).desc()).limit(5).all()

            results[name] = {
                "total": total,
                "by_year": by_year,
                "top_programs": [{"name": n, "count": c} for n, c in top_progs],
            }

        return {"type": "institution_comparison", "entities": results}

    if programs:
        names = [n.strip() for n in programs.split(",")]
        results = {}
        for name in names:
            rows = session.query(
                extract('year', Announcement.date).label('year'),
                func.count(Project.id).label('count'),
            ).select_from(Project
            ).join(Announcement, Project.announcement_id == Announcement.id
            ).join(Program, Announcement.program_id == Program.id
            ).filter(Program.name.contains(name), Announcement.date.isnot(None)
            ).group_by('year').order_by('year').all()

            total = sum(c for _, c in rows)
            by_year = {int(y): c for y, c in rows}

            # Top institutions for this program
            top_inst = session.query(
                Institution.name, func.count(Project.id).label('count'),
            ).select_from(Project
            ).join(Announcement, Project.announcement_id == Announcement.id
            ).join(Program, Announcement.program_id == Program.id
            ).join(Institution, Project.institution_id == Institution.id
            ).filter(Program.name.contains(name)
            ).group_by(Institution.name).order_by(func.count(Project.id).desc()).limit(5).all()

            results[name] = {
                "total": total,
                "by_year": by_year,
                "top_institutions": [{"name": n, "count": c} for n, c in top_inst],
            }

        return {"type": "program_comparison", "entities": results}


@router.get("/programs/{program_name}")
def program_detail(program_name: str):
    """Get detailed analytics for a specific program."""
    from api.main import get_db
    session = next(get_db())

    program = session.query(Program).filter(Program.name.contains(program_name)).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # Projects over time
    by_year = session.query(
        extract('year', Announcement.date).label('year'),
        func.count(Project.id).label('count'),
    ).join(Project, Announcement.id == Project.announcement_id
    ).filter(Announcement.program_id == program.id, Announcement.date.isnot(None)
    ).group_by('year').order_by('year').all()

    # Top institutions
    top_institutions = session.query(
        Institution.name, func.count(Project.id).label('count'),
    ).select_from(Project
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Institution, Project.institution_id == Institution.id
    ).filter(Announcement.program_id == program.id
    ).group_by(Institution.name).order_by(func.count(Project.id).desc()).limit(10).all()

    # Top researchers
    top_researchers = session.query(
        Researcher.name, func.count(Project.id).label('count'),
    ).select_from(Project
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Researcher, Project.researcher_id == Researcher.id
    ).filter(Announcement.program_id == program.id
    ).group_by(Researcher.name).order_by(func.count(Project.id).desc()).limit(10).all()

    total = session.query(Project).join(
        Announcement, Project.announcement_id == Announcement.id
    ).filter(Announcement.program_id == program.id).count()

    return {
        "name": program.name,
        "total_projects": total,
        "by_year": {int(y): c for y, c in by_year},
        "top_institutions": [{"name": n, "count": c} for n, c in top_institutions],
        "top_researchers": [{"name": n, "count": c} for n, c in top_researchers],
    }


@router.get("/institutions/{institution_name}")
def institution_detail(institution_name: str):
    """Get detailed analytics for a specific institution."""
    from api.main import get_db
    session = next(get_db())

    institution = session.query(Institution).filter(
        Institution.name.contains(institution_name)
    ).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Projects over time
    by_year = session.query(
        extract('year', Announcement.date).label('year'),
        func.count(Project.id).label('count'),
    ).join(Project, Announcement.id == Project.announcement_id
    ).filter(Project.institution_id == institution.id, Announcement.date.isnot(None)
    ).group_by('year').order_by('year').all()

    # Top programs
    top_programs = session.query(
        Program.name, func.count(Project.id).label('count'),
    ).select_from(Project
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Program, Announcement.program_id == Program.id
    ).filter(Project.institution_id == institution.id
    ).group_by(Program.name).order_by(func.count(Project.id).desc()).limit(10).all()

    # Top researchers
    top_researchers = session.query(
        Researcher.name, func.count(Project.id).label('count'),
    ).select_from(Project
    ).join(Researcher, Project.researcher_id == Researcher.id
    ).filter(Project.institution_id == institution.id
    ).group_by(Researcher.name).order_by(func.count(Project.id).desc()).limit(10).all()

    total = session.query(Project).filter(
        Project.institution_id == institution.id
    ).count()

    return {
        "name": institution.name,
        "total_projects": total,
        "by_year": {int(y): c for y, c in by_year},
        "top_programs": [{"name": n, "count": c} for n, c in top_programs],
        "top_researchers": [{"name": n, "count": c} for n, c in top_researchers],
    }


@router.get("/young_researchers")
def young_researcher_stats(
    year: Optional[int] = Query(None, description="Filter by year"),
    top_n: int = Query(10, le=50, description="Number of results"),
):
    """Statistics on young researcher programs."""
    from api.main import get_db
    session = next(get_db())

    base = session.query(Project).join(
        Announcement, Project.announcement_id == Announcement.id
    ).filter(Announcement.young_researcher_flag == True)
    if year:
        base = base.filter(extract('year', Announcement.date) == year)

    total = base.count()

    # By year
    by_year = session.query(
        extract('year', Announcement.date).label('year'),
        func.count(Project.id).label('count'),
    ).join(Project, Announcement.id == Project.announcement_id
    ).filter(Announcement.young_researcher_flag == True, Announcement.date.isnot(None)
    ).group_by('year').order_by('year').all()

    # Top institutions
    top_institutions = session.query(
        Institution.name, func.count(Project.id).label('count'),
    ).select_from(Project
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Institution, Project.institution_id == Institution.id
    ).filter(Announcement.young_researcher_flag == True
    ).group_by(Institution.name).order_by(func.count(Project.id).desc()).limit(top_n).all()

    # Top programs
    top_programs = session.query(
        Program.name, func.count(Project.id).label('count'),
    ).select_from(Project
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Program, Announcement.program_id == Program.id
    ).filter(Announcement.young_researcher_flag == True
    ).group_by(Program.name).order_by(func.count(Project.id).desc()).limit(top_n).all()

    return {
        "total_projects": total,
        "by_year": {int(y): c for y, c in by_year},
        "top_institutions": [{"name": n, "count": c} for n, c in top_institutions],
        "top_programs": [{"name": n, "count": c} for n, c in top_programs],
    }


@router.get("/keyword_search")
def keyword_analysis(
    keywords: str = Query(..., description="Comma-separated keywords to analyze in project titles"),
):
    """Analyze keyword frequency in project titles over time."""
    from api.main import get_db
    session = next(get_db())

    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not kw_list:
        raise HTTPException(status_code=400, detail="Provide at least one keyword")

    results = {}
    for kw in kw_list:
        rows = session.query(
            extract('year', Announcement.date).label('year'),
            func.count(Project.id).label('count'),
        ).join(Project, Announcement.id == Project.announcement_id
        ).filter(Project.title.contains(kw), Announcement.date.isnot(None)
        ).group_by('year').order_by('year').all()

        total = sum(c for _, c in rows)
        results[kw] = {
            "total": total,
            "by_year": {int(y): c for y, c in rows},
        }

    return {"keywords": results}


@router.get("/collaborations")
def collaboration_network(
    institution: Optional[str] = Query(None, description="Institution name to find collaborators for"),
    program: Optional[str] = Query(None, description="Program name to find participating institutions"),
    top_n: int = Query(20, le=100, description="Number of results"),
):
    """Find institutions that co-participate in the same programs, or find all institutions in a program."""
    from api.main import get_db
    session = next(get_db())

    if not institution and not program:
        raise HTTPException(status_code=400, detail="Provide 'institution' or 'program' parameter")

    if institution:
        # Find programs this institution participates in
        inst = session.query(Institution).filter(Institution.name.contains(institution)).first()
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")

        program_ids = [
            pid for (pid,) in session.query(Announcement.program_id).join(
                Project, Announcement.id == Project.announcement_id
            ).filter(Project.institution_id == inst.id).distinct().all()
            if pid
        ]

        # Find other institutions in those programs
        co_institutions = session.query(
            Institution.name, func.count(Project.id).label('count'),
        ).select_from(Project
        ).join(Announcement, Project.announcement_id == Announcement.id
        ).join(Institution, Project.institution_id == Institution.id
        ).filter(
            Announcement.program_id.in_(program_ids),
            Institution.id != inst.id,
        ).group_by(Institution.name).order_by(func.count(Project.id).desc()).limit(top_n).all()

        # Shared programs
        shared_programs = session.query(
            Program.name, func.count(Project.id).label('count'),
        ).select_from(Project
        ).join(Announcement, Project.announcement_id == Announcement.id
        ).join(Program, Announcement.program_id == Program.id
        ).filter(
            Announcement.program_id.in_(program_ids)
        ).group_by(Program.name).order_by(func.count(Project.id).desc()).limit(10).all()

        return {
            "institution": inst.name,
            "co_institutions": [{"name": n, "shared_projects": c} for n, c in co_institutions],
            "shared_programs": [{"name": n, "count": c} for n, c in shared_programs],
        }

    if program:
        prog = session.query(Program).filter(Program.name.contains(program)).first()
        if not prog:
            raise HTTPException(status_code=404, detail="Program not found")

        participants = session.query(
            Institution.name, func.count(Project.id).label('count'),
        ).select_from(Project
        ).join(Announcement, Project.announcement_id == Announcement.id
        ).join(Institution, Project.institution_id == Institution.id
        ).filter(Announcement.program_id == prog.id
        ).group_by(Institution.name).order_by(func.count(Project.id).desc()).limit(top_n).all()

        return {
            "program": prog.name,
            "participating_institutions": [{"name": n, "project_count": c} for n, c in participants],
        }
