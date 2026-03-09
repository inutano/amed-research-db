"""
Import parsed data into database
"""
import json
from pathlib import Path
from datetime import datetime
from models import init_db, get_session, Program, Institution, Researcher, Announcement, Project

def import_data(json_path, db_path='sqlite:///amed.db'):
    # Initialize database
    engine = init_db(db_path)
    session = get_session(engine)
    
    # Load parsed data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Importing {len(data)} announcements...")
    
    for item in data:
        # Get or create program
        program = session.query(Program).filter_by(name=item['program_name']).first()
        if not program:
            program = Program(name=item['program_name'])
            session.add(program)
            session.flush()
        
        # Create announcement
        announcement = Announcement(
            url=item['url'],
            page_title=item['page_title'],
            program_id=program.id,
            date=datetime.strptime(item['date'], '%Y-%m-%d').date() if item['date'] else None,
            young_researcher_flag=item['young_researcher_flag']
        )
        session.add(announcement)
        session.flush()
        
        # Import projects
        for proj in item['projects']:
            if not proj['title'] or proj['title'] == '研究開発代表者名':
                continue
            
            # Get or create institution
            institution = None
            if proj['institution']:
                institution = session.query(Institution).filter_by(name=proj['institution']).first()
                if not institution:
                    institution = Institution(name=proj['institution'])
                    session.add(institution)
                    session.flush()
            
            # Get or create researcher
            researcher = None
            if proj['researcher']:
                researcher = session.query(Researcher).filter_by(name=proj['researcher']).first()
                if not researcher:
                    researcher = Researcher(name=proj['researcher'])
                    session.add(researcher)
                    session.flush()
            
            # Create project
            project = Project(
                announcement_id=announcement.id,
                title=proj['title'],
                researcher_id=researcher.id if researcher else None,
                institution_id=institution.id if institution else None,
                position=proj['position']
            )
            session.add(project)
    
    session.commit()
    
    # Print statistics
    print(f"\nImport complete!")
    print(f"Programs: {session.query(Program).count()}")
    print(f"Institutions: {session.query(Institution).count()}")
    print(f"Researchers: {session.query(Researcher).count()}")
    print(f"Announcements: {session.query(Announcement).count()}")
    print(f"Projects: {session.query(Project).count()}")
    
    session.close()

if __name__ == '__main__':
    data_path = Path(__file__).parent.parent / 'data' / 'parsed_samples.json'
    db_path = Path(__file__).parent / 'amed.db'
    import_data(data_path, f'sqlite:///{db_path}')
