"""
Check which URLs are already in the database
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'database'))

from models import get_engine, get_session, Announcement
import json

def get_scraped_urls():
    """Get all URLs already in database"""
    db_path = Path(__file__).parent.parent / 'database' / 'amed.db'
    engine = get_engine(f'sqlite:///{db_path}')
    session = get_session(engine)
    
    urls = [ann.url for ann in session.query(Announcement.url).all()]
    session.close()
    return set(urls)

def get_new_urls(all_urls):
    """Filter URLs not yet in database"""
    scraped = get_scraped_urls()
    return [url for url in all_urls if url not in scraped]

if __name__ == '__main__':
    # Load project links
    links_file = Path(__file__).parent.parent / 'data' / 'project_links.json'
    with open(links_file, 'r', encoding='utf-8') as f:
        links = json.load(f)
    
    all_urls = [link['url'] for link in links]
    scraped_urls = get_scraped_urls()
    new_urls = get_new_urls(all_urls)
    
    print(f"Total URLs: {len(all_urls)}")
    print(f"In database: {len(scraped_urls)}")
    print(f"New URLs: {len(new_urls)}")
    
    if new_urls:
        print(f"\nFirst 5 new URLs:")
        for url in new_urls[:5]:
            print(f"  {url}")
