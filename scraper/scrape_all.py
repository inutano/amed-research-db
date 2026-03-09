"""
Production scraper for AMED website with respectful rate limiting
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import random
from pathlib import Path
from datetime import datetime
import sys

# Add database module to path
sys.path.append(str(Path(__file__).parent.parent / 'database'))
from models import get_engine, get_session, Announcement

BASE_URL = "https://www.amed.go.jp"
LISTING_URL = f"{BASE_URL}/koubo/saitaku_index.html"

# Respectful scraping configuration
CONFIG = {
    'delay_min': 2,      # Minimum delay between requests (seconds)
    'delay_max': 4,      # Maximum delay (random between min-max)
    'user_agent': 'AMED Research Database Bot (Academic Research)',
    'timeout': 30,       # Request timeout
    'max_retries': 3,    # Max retries on failure
    'retry_delay': 10,   # Delay before retry
    'batch_size': 50,    # Save progress every N pages
    'respect_hours': (9, 18),  # Only scrape during business hours JST (optional)
}

class RespectfulScraper:
    def __init__(self, config=CONFIG):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en;q=0.9',
        })
        self.request_count = 0
        self.start_time = time.time()
    
    def wait(self):
        """Random delay between requests"""
        delay = random.uniform(self.config['delay_min'], self.config['delay_max'])
        print(f"  Waiting {delay:.1f}s...", end='\r')
        time.sleep(delay)
    
    def fetch(self, url, retries=0):
        """Fetch URL with retry logic"""
        try:
            self.wait()
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            self.request_count += 1
            return response.text
        except requests.RequestException as e:
            if retries < self.config['max_retries']:
                print(f"\n  Error: {e}. Retrying in {self.config['retry_delay']}s...")
                time.sleep(self.config['retry_delay'])
                return self.fetch(url, retries + 1)
            else:
                print(f"\n  Failed after {self.config['max_retries']} retries: {e}")
                return None
    
    def stats(self):
        """Print scraping statistics"""
        elapsed = time.time() - self.start_time
        rate = self.request_count / elapsed if elapsed > 0 else 0
        print(f"\nStats: {self.request_count} requests in {elapsed:.1f}s ({rate:.2f} req/s)")

def load_progress(progress_file):
    """Load scraping progress"""
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'completed': [], 'failed': []}

def get_db_urls():
    """Get URLs already in database"""
    db_path = Path(__file__).parent.parent / 'database' / 'amed.db'
    if not db_path.exists():
        return set()
    
    engine = get_engine(f'sqlite:///{db_path}')
    session = get_session(engine)
    urls = set([ann.url for ann in session.query(Announcement.url).all()])
    session.close()
    return urls

def save_progress(progress_file, progress):
    """Save scraping progress"""
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def main():
    print("="*60)
    print("AMED Research Database - Production Scraper")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Delay: {CONFIG['delay_min']}-{CONFIG['delay_max']}s between requests")
    print(f"  Timeout: {CONFIG['timeout']}s")
    print(f"  Max retries: {CONFIG['max_retries']}")
    print(f"  Batch size: {CONFIG['batch_size']} (save progress)")
    print(f"  User-Agent: {CONFIG['user_agent']}")
    
    # Confirm before starting
    print(f"\nThis will scrape ~971 pages. Estimated time: ~45-80 minutes")
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return
    
    scraper = RespectfulScraper()
    output_dir = Path(__file__).parent.parent / 'data'
    output_dir.mkdir(exist_ok=True)
    
    progress_file = output_dir / 'scraping_progress.json'
    progress = load_progress(progress_file)
    
    # Load project links
    links_file = output_dir / 'project_links.json'
    if not links_file.exists():
        print("\nFetching project links...")
        html = scraper.fetch(LISTING_URL)
        if not html:
            print("Failed to fetch listing page")
            return
        
        soup = BeautifulSoup(html, 'lxml')
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/koubo/' in href and 'C_' in href:
                full_url = f"{BASE_URL}{href}" if href.startswith('/') else href
                links.append({
                    'url': full_url,
                    'text': link.get_text(strip=True)
                })
        
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(links, f, ensure_ascii=False, indent=2)
        print(f"Found {len(links)} project links")
    else:
        with open(links_file, 'r', encoding='utf-8') as f:
            links = json.load(f)
        print(f"Loaded {len(links)} project links from cache")
    
    # Filter out already completed
    completed_urls = set(progress['completed'])
    db_urls = get_db_urls()
    already_done = completed_urls | db_urls
    remaining = [l for l in links if l['url'] not in already_done]
    
    print(f"\nProgress:")
    print(f"  In database: {len(db_urls)}")
    print(f"  Scraped (not imported): {len(completed_urls - db_urls)}")
    print(f"  Total completed: {len(already_done)}/{len(links)}")
    print(f"  Remaining: {len(remaining)} pages")
    
    if not remaining:
        print("\nAll pages already scraped!")
        return
    
    # Scrape remaining pages
    print(f"\nStarting scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)
    
    all_projects = []
    total_completed = len(progress['completed'])
    
    for i, link in enumerate(remaining, 1):
        overall_progress = total_completed + i
        percent = (overall_progress / len(links)) * 100
        print(f"\n[{i}/{len(remaining)}] Overall: {overall_progress}/{len(links)} ({percent:.1f}%)")
        print(f"  {link['text'][:70]}...")
        
        html = scraper.fetch(link['url'])
        if html:
            all_projects.append({
                'url': link['url'],
                'text': link['text'],
                'html': html,
                'scraped_at': datetime.now().isoformat()
            })
            progress['completed'].append(link['url'])
        else:
            progress['failed'].append(link['url'])
        
        # Save progress periodically
        if i % CONFIG['batch_size'] == 0:
            overall = total_completed + i
            print(f"\n  ✓ Checkpoint: {overall}/{len(links)} pages ({(overall/len(links)*100):.1f}%)")
            print(f"  Saving progress...")
            save_progress(progress_file, progress)
            
            # Save scraped data
            output_file = output_dir / f'scraped_projects_batch_{i}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_projects, f, ensure_ascii=False, indent=2)
            all_projects = []  # Clear memory
            
            scraper.stats()
    
    # Final save
    print("\n\n" + "="*60)
    print("SCRAPING COMPLETE")
    print("="*60)
    print(f"\nSaving final results...")
    save_progress(progress_file, progress)
    
    if all_projects:
        output_file = output_dir / f'scraped_projects_final.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_projects, f, ensure_ascii=False, indent=2)
    
    scraper.stats()
    
    total_in_db = len(get_db_urls())
    print(f"\n📊 Final Statistics:")
    print(f"  Total pages: {len(links)}")
    print(f"  In database: {total_in_db}")
    print(f"  Newly scraped: {len(progress['completed'])}")
    print(f"  Failed: {len(progress['failed'])}")
    print(f"  Completion: {((total_in_db + len(progress['completed']))/len(links)*100):.1f}%")
    print(f"\n✓ Finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if progress['failed']:
        print(f"\nFailed URLs saved in {progress_file}")

if __name__ == '__main__':
    main()
