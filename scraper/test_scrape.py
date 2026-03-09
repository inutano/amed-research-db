"""
Test scraper to fetch sample data from AMED website
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

BASE_URL = "https://www.amed.go.jp"
LISTING_URL = f"{BASE_URL}/koubo/saitaku_index.html"

def fetch_listing_page():
    """Fetch the main listing page"""
    print(f"Fetching {LISTING_URL}...")
    response = requests.get(LISTING_URL)
    response.raise_for_status()
    return response.text

def parse_listing_page(html):
    """Parse listing page and extract project URLs"""
    soup = BeautifulSoup(html, 'lxml')
    links = []
    
    # Find all links to adoption announcements
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/koubo/' in href and 'C_' in href:
            full_url = f"{BASE_URL}{href}" if href.startswith('/') else href
            text = link.get_text(strip=True)
            links.append({
                'url': full_url,
                'text': text
            })
    
    return links

def fetch_project_page(url):
    """Fetch individual project page"""
    print(f"Fetching {url}...")
    time.sleep(1)  # Be respectful
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def main():
    # Fetch listing page
    html = fetch_listing_page()
    
    # Parse and get project links
    links = parse_listing_page(html)
    print(f"Found {len(links)} project links")
    
    # Save links to file
    output_dir = Path(__file__).parent.parent / 'data'
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / 'project_links.json', 'w', encoding='utf-8') as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(links)} links to data/project_links.json")
    
    # Fetch first 3 projects as samples
    sample_projects = []
    for i, link in enumerate(links[:3]):
        try:
            html = fetch_project_page(link['url'])
            sample_projects.append({
                'url': link['url'],
                'text': link['text'],
                'html': html
            })
        except Exception as e:
            print(f"Error fetching {link['url']}: {e}")
    
    # Save sample HTML
    with open(output_dir / 'sample_projects.json', 'w', encoding='utf-8') as f:
        json.dump(sample_projects, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(sample_projects)} sample projects to data/sample_projects.json")

if __name__ == '__main__':
    main()
