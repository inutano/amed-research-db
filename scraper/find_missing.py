"""
Re-scrape missing pages that are in progress but not in database
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'database'))
from models import get_engine, get_session, Announcement

# Load progress
data_dir = Path(__file__).parent.parent / 'data'
with open(data_dir / 'scraping_progress.json', 'r') as f:
    progress = json.load(f)

with open(data_dir / 'project_links.json', 'r') as f:
    all_links = json.load(f)

# Get DB URLs
db_path = Path(__file__).parent.parent / 'database' / 'amed.db'
engine = get_engine(f'sqlite:///{db_path}')
session = get_session(engine)
db_urls = set([ann.url for ann in session.query(Announcement.url).all()])
session.close()

# Find missing
completed_urls = set(progress['completed'])
missing_urls = completed_urls - db_urls

print(f"Completed in progress: {len(completed_urls)}")
print(f"In database: {len(db_urls)}")
print(f"Missing (need to re-scrape): {len(missing_urls)}")

# Create new links file for missing
missing_links = [l for l in all_links if l['url'] in missing_urls]

output_file = data_dir / 'missing_links.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(missing_links, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(missing_links)} missing links to {output_file}")
print("\nTo re-scrape these, temporarily replace project_links.json with missing_links.json")
