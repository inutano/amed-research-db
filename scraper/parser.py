"""
Parser to extract structured data from AMED project pages
"""
from bs4 import BeautifulSoup
import re
from datetime import datetime

def parse_project_page(html, url):
    """Parse a project page and extract structured data"""
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract title
    title_elem = soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else None
    
    # Extract date from title or page
    date_match = re.search(r'(令和|平成)(\d+)年(\d+)月(\d+)日', html)
    date_str = None
    if date_match:
        era, year, month, day = date_match.groups()
        # Convert Japanese era to Western year
        year_offset = 2018 if era == '令和' else 1988
        western_year = int(year) + year_offset
        date_str = f"{western_year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Extract program name from title
    program_name = None
    if title:
        match = re.search(r'「(.+?)」', title)
        if match:
            program_name = match.group(1)
    
    # Extract project table - look for tables with researcher data
    projects = []
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            # Look for rows with 4-5 columns (title, researcher, institution, position)
            if len(cols) >= 4:
                researcher = cols[-3].get_text(strip=True)
                institution = cols[-2].get_text(strip=True)
                position = cols[-1].get_text(strip=True)
                title = cols[-4].get_text(strip=True)
                
                # Skip header rows
                if researcher in ['研究代表者', '研究開発代表者名', '所属機関']:
                    continue
                if not researcher or not title:
                    continue
                    
                project = {
                    'title': title,
                    'researcher': researcher,
                    'institution': institution,
                    'position': position,
                }
                projects.append(project)
    
    # Check for young researcher flag
    young_researcher = '若手あり' in html or '若手' in html
    
    return {
        'url': url,
        'page_title': title,
        'program_name': program_name,
        'date': date_str,
        'young_researcher_flag': young_researcher,
        'projects': projects
    }

if __name__ == '__main__':
    import json
    from pathlib import Path
    
    # Load sample projects
    data_dir = Path(__file__).parent.parent / 'data'
    with open(data_dir / 'sample_projects.json', 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    # Parse each sample
    parsed = []
    for sample in samples:
        result = parse_project_page(sample['html'], sample['url'])
        parsed.append(result)
        print(f"\nParsed: {result['page_title']}")
        print(f"  Program: {result['program_name']}")
        print(f"  Date: {result['date']}")
        print(f"  Projects: {len(result['projects'])}")
    
    # Save parsed data
    with open(data_dir / 'parsed_samples.json', 'w', encoding='utf-8') as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved parsed data to data/parsed_samples.json")
