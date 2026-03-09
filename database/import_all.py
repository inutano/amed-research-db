"""
Import all scraped projects into database
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent / 'database'))
sys.path.append(str(Path(__file__).parent.parent / 'scraper'))

from models import init_db, get_session, Program, Institution, Researcher, Announcement, Project
from parser import parse_project_page

def import_batch(batch_file, session):
    """Import a batch of scraped projects"""
    with open(batch_file, 'r', encoding='utf-8') as f:
        batch = json.load(f)
    
    imported = 0
    skipped = 0
    
    for item in batch:
        # Check if already exists
        existing = session.query(Announcement).filter_by(url=item['url']).first()
        if existing:
            skipped += 1
            continue
        
        # Parse HTML
        parsed = parse_project_page(item['html'], item['url'])
        
        if not parsed['program_name']:
            skipped += 1
            continue
        
        # Get or create program
        program = session.query(Program).filter_by(name=parsed['program_name']).first()
        if not program:
            program = Program(name=parsed['program_name'])
            session.add(program)
            session.flush()
        
        # Create announcement
        date_obj = None
        if parsed['date']:
            try:
                # Normalize full-width numbers to half-width
                date_str = parsed['date'].replace('０', '0').replace('１', '1').replace('２', '2').replace('３', '3').replace('４', '4').replace('５', '5').replace('６', '6').replace('７', '7').replace('８', '8').replace('９', '9')
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                pass
        
        announcement = Announcement(
            url=parsed['url'],
            page_title=parsed['page_title'],
            program_id=program.id,
            date=date_obj,
            young_researcher_flag=parsed['young_researcher_flag']
        )
        session.add(announcement)
        session.flush()
        
        # Import projects
        for proj in parsed['projects']:
            if not proj['title'] or not proj['researcher']:
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
        
        imported += 1
    
    session.commit()
    return imported, skipped

def main():
    print("="*60)
    print("AMED Database Import")
    print("="*60)
    
    # Initialize database
    db_path = Path(__file__).parent.parent / 'database' / 'amed.db'
    engine = init_db(f'sqlite:///{db_path}')
    session = get_session(engine)
    
    # Find all batch files
    data_dir = Path(__file__).parent.parent / 'data'
    batch_files = sorted(data_dir.glob('scraped_projects_batch_*.json'))
    final_file = data_dir / 'scraped_projects_final.json'
    if final_file.exists():
        batch_files.append(final_file)
    
    print(f"\nFound {len(batch_files)} batch files to import")
    print(f"Database: {db_path}")
    
    # Import each batch
    total_imported = 0
    total_skipped = 0
    
    for i, batch_file in enumerate(batch_files, 1):
        print(f"\n[{i}/{len(batch_files)}] Processing {batch_file.name}...")
        imported, skipped = import_batch(batch_file, session)
        total_imported += imported
        total_skipped += skipped
        print(f"  Imported: {imported}, Skipped: {skipped}")
    
    # Print final statistics
    print("\n" + "="*60)
    print("IMPORT COMPLETE")
    print("="*60)
    print(f"\n📊 Statistics:")
    print(f"  Announcements imported: {total_imported}")
    print(f"  Announcements skipped: {total_skipped}")
    print(f"  Total programs: {session.query(Program).count()}")
    print(f"  Total institutions: {session.query(Institution).count()}")
    print(f"  Total researchers: {session.query(Researcher).count()}")
    print(f"  Total announcements: {session.query(Announcement).count()}")
    print(f"  Total projects: {session.query(Project).count()}")
    
    session.close()
    print(f"\n✓ Database updated: {db_path}")

if __name__ == '__main__':
    main()
