"""
MCP Server for AMED Research Database.

Exposes the database as tools that LLMs can call directly.
Run with: python mcp_server.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, or_, extract
from database.models import (
    get_engine, get_session, Program, Institution, Researcher, Announcement, Project,
)

DB_PATH = Path(__file__).parent / "database" / "amed.db"
engine = get_engine(f"sqlite:///{DB_PATH}")

mcp = FastMCP(
    "AMED Research Database",
    instructions=(
        "Query the AMED (Japan Agency for Medical Research and Development) "
        "research project database. Contains ~3800 projects, 3000+ researchers, "
        "700+ institutions, and 200+ programs from 2015-2026. "
        "Use search_projects for keyword/filter queries, get_stats for overview, "
        "and analytics tools for trends and comparisons."
    ),
)


def _get_session():
    return get_session(engine)


@mcp.tool()
def search_projects(
    query: str = "",
    year: int = 0,
    institution: str = "",
    researcher: str = "",
    program: str = "",
    limit: int = 20,
) -> str:
    """Search AMED research projects with filters.

    Args:
        query: Free-text search in title, researcher, institution (e.g. "がん", "AI")
        year: Filter by year (e.g. 2024)
        institution: Filter by institution name (partial match, e.g. "東京大学")
        researcher: Filter by researcher name (partial match)
        program: Filter by program name (partial match)
        limit: Max results to return (default 20, max 100)
    """
    session = _get_session()
    q = session.query(
        Project, Researcher, Institution, Program, Announcement,
    ).join(Researcher, Project.researcher_id == Researcher.id, isouter=True
    ).join(Institution, Project.institution_id == Institution.id, isouter=True
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Program, Announcement.program_id == Program.id, isouter=True)

    if query:
        q = q.filter(or_(
            Project.title.contains(query),
            Researcher.name.contains(query),
            Institution.name.contains(query),
        ))
    if year:
        q = q.filter(extract("year", Announcement.date) == year)
    if institution:
        q = q.filter(Institution.name.contains(institution))
    if researcher:
        q = q.filter(Researcher.name.contains(researcher))
    if program:
        q = q.filter(Program.name.contains(program))

    total = q.count()
    limit = min(limit, 100)
    results = q.limit(limit).all()

    lines = [f"Found {total} projects (showing {len(results)}):"]
    for proj, res, inst, prog, ann in results:
        date_str = str(ann.date) if ann.date else "?"
        lines.append(
            f"- [{date_str}] {proj.title}\n"
            f"  Researcher: {res.name if res else '?'} | "
            f"Institution: {inst.name if inst else '?'} | "
            f"Program: {prog.name if prog else '?'}"
        )
    session.close()
    return "\n".join(lines)


@mcp.tool()
def get_stats() -> str:
    """Get overview statistics of the AMED database."""
    session = _get_session()
    result = {
        "projects": session.query(Project).count(),
        "researchers": session.query(Researcher).count(),
        "institutions": session.query(Institution).count(),
        "programs": session.query(Program).count(),
        "announcements": session.query(Announcement).count(),
    }

    # Year distribution
    years = session.query(
        extract("year", Announcement.date).label("year"),
        func.count(Project.id).label("count"),
    ).join(Project).group_by("year").order_by("year").all()

    lines = [
        f"AMED Database Statistics:",
        f"  Projects: {result['projects']}",
        f"  Researchers: {result['researchers']}",
        f"  Institutions: {result['institutions']}",
        f"  Programs: {result['programs']}",
        f"\nProjects by year:",
    ]
    for y, c in years:
        if y:
            lines.append(f"  {int(y)}: {c}")
    session.close()
    return "\n".join(lines)


@mcp.tool()
def top_institutions(top_n: int = 10, year: int = 0) -> str:
    """Get top institutions by project count.

    Args:
        top_n: Number of institutions to return (default 10)
        year: Optional year filter
    """
    session = _get_session()
    q = session.query(
        Institution.name, func.count(Project.id).label("count"),
    ).select_from(Project
    ).join(Institution, Project.institution_id == Institution.id
    ).join(Announcement, Project.announcement_id == Announcement.id)

    if year:
        q = q.filter(extract("year", Announcement.date) == year)

    results = q.group_by(Institution.name).order_by(
        func.count(Project.id).desc()
    ).limit(top_n).all()

    title = f"Top {top_n} institutions" + (f" ({year})" if year else "")
    lines = [f"{title}:"]
    for i, (name, count) in enumerate(results, 1):
        lines.append(f"  {i}. {name}: {count} projects")
    session.close()
    return "\n".join(lines)


@mcp.tool()
def compare_institutions(names: str) -> str:
    """Compare institutions side by side.

    Args:
        names: Comma-separated institution names (e.g. "東京大学,京都大学,大阪大学")
    """
    session = _get_session()
    name_list = [n.strip() for n in names.split(",")]

    lines = [f"Institution comparison:"]
    for name in name_list:
        rows = session.query(
            extract("year", Announcement.date).label("year"),
            func.count(Project.id).label("count"),
        ).select_from(Project
        ).join(Announcement, Project.announcement_id == Announcement.id
        ).join(Institution, Project.institution_id == Institution.id
        ).filter(Institution.name.contains(name), Announcement.date.isnot(None)
        ).group_by("year").order_by("year").all()

        total = sum(c for _, c in rows)
        year_str = ", ".join(f"{int(y)}:{c}" for y, c in rows)
        lines.append(f"\n{name} ({total} total): {year_str}")

        # Top programs
        top_progs = session.query(
            Program.name, func.count(Project.id).label("count"),
        ).select_from(Project
        ).join(Announcement, Project.announcement_id == Announcement.id
        ).join(Program, Announcement.program_id == Program.id
        ).join(Institution, Project.institution_id == Institution.id
        ).filter(Institution.name.contains(name)
        ).group_by(Program.name).order_by(func.count(Project.id).desc()).limit(3).all()
        for pname, pcount in top_progs:
            lines.append(f"  - {pname}: {pcount}")

    session.close()
    return "\n".join(lines)


@mcp.tool()
def keyword_trends(keywords: str) -> str:
    """Analyze keyword frequency in project titles over time.

    Args:
        keywords: Comma-separated keywords (e.g. "AI,ゲノム,がん,感染症")
    """
    session = _get_session()
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]

    lines = ["Keyword trends in project titles:"]
    for kw in kw_list:
        rows = session.query(
            extract("year", Announcement.date).label("year"),
            func.count(Project.id).label("count"),
        ).join(Project, Announcement.id == Project.announcement_id
        ).filter(Project.title.contains(kw), Announcement.date.isnot(None)
        ).group_by("year").order_by("year").all()

        total = sum(c for _, c in rows)
        year_str = ", ".join(f"{int(y)}:{c}" for y, c in rows)
        lines.append(f"\n\"{kw}\" ({total} total): {year_str}")

    session.close()
    return "\n".join(lines)


@mcp.tool()
def researcher_profile(name: str) -> str:
    """Get researcher profile with their projects.

    Args:
        name: Researcher name (partial match, e.g. "田中")
    """
    session = _get_session()
    researcher = session.query(Researcher).filter(
        Researcher.name.contains(name)
    ).first()

    if not researcher:
        session.close()
        return f"Researcher '{name}' not found."

    projects = session.query(
        Project, Institution, Program, Announcement,
    ).join(Institution, Project.institution_id == Institution.id, isouter=True
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Program, Announcement.program_id == Program.id, isouter=True
    ).filter(Project.researcher_id == researcher.id).all()

    lines = [f"Researcher: {researcher.name}", f"Projects: {len(projects)}"]
    for proj, inst, prog, ann in projects:
        date_str = str(ann.date) if ann.date else "?"
        lines.append(
            f"  - [{date_str}] {proj.title}\n"
            f"    {inst.name if inst else '?'} | {prog.name if prog else '?'}"
        )
    session.close()
    return "\n".join(lines)


@mcp.tool()
def find_collaborators(institution: str, top_n: int = 10) -> str:
    """Find institutions that collaborate in the same programs.

    Args:
        institution: Institution name (partial match)
        top_n: Number of collaborators to return
    """
    session = _get_session()
    inst = session.query(Institution).filter(
        Institution.name.contains(institution)
    ).first()
    if not inst:
        session.close()
        return f"Institution '{institution}' not found."

    program_ids = [
        pid for (pid,) in session.query(Announcement.program_id).join(
            Project, Announcement.id == Project.announcement_id
        ).filter(Project.institution_id == inst.id).distinct().all()
        if pid
    ]

    co_institutions = session.query(
        Institution.name, func.count(Project.id).label("count"),
    ).select_from(Project
    ).join(Announcement, Project.announcement_id == Announcement.id
    ).join(Institution, Project.institution_id == Institution.id
    ).filter(
        Announcement.program_id.in_(program_ids),
        Institution.id != inst.id,
    ).group_by(Institution.name).order_by(
        func.count(Project.id).desc()
    ).limit(top_n).all()

    lines = [f"Institutions co-participating with {inst.name}:"]
    for name, count in co_institutions:
        lines.append(f"  - {name}: {count} shared program projects")
    session.close()
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
