"""Quick database queries for testing"""
from models import get_engine, get_session, Program, Institution, Researcher, Project
from sqlalchemy import func

engine = get_engine('sqlite:///amed.db')
session = get_session(engine)

print("=== AMED Research Database ===\n")

# Overall stats
print("Overall Statistics:")
print(f"  Programs: {session.query(Program).count()}")
print(f"  Institutions: {session.query(Institution).count()}")
print(f"  Researchers: {session.query(Researcher).count()}")
print(f"  Projects: {session.query(Project).count()}\n")

# Top institutions
print("Top Institutions by Project Count:")
results = session.query(
    Institution.name, 
    func.count(Project.id).label('count')
).join(Project).group_by(Institution.name).order_by(func.count(Project.id).desc()).limit(5).all()
for name, count in results:
    print(f"  {name}: {count}")

print("\nSample Projects:")
projects = session.query(Project, Researcher, Institution).join(
    Researcher
).join(Institution).limit(3).all()
for proj, researcher, institution in projects:
    print(f"  • {proj.title[:60]}...")
    print(f"    {researcher.name} ({institution.name}, {proj.position})\n")

session.close()
