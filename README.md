# AMED Research Database API

A REST API for accessing and analyzing research proposals accepted by AMED (Japan Agency for Medical Research and Development).

## Overview

This project collects data from AMED's public website and provides a searchable database with analytics capabilities through a REST API, designed to be consumed by LLMs and AI agents.

## Architecture

```
┌─────────────────────────────────────────┐
│   LLM/AI Agent (Claude, GPT, etc.)     │
│   via Kiro-CLI or direct API calls     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│   FastAPI Server                        │
│   - Search & filter projects            │
│   - Statistics & analytics              │
│   - Trend analysis                      │
│   - Network analysis                    │
│   - OpenAPI documentation               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│   PostgreSQL/SQLite Database            │
│   - Projects                            │
│   - Researchers                         │
│   - Institutions                        │
│   - Relationships                       │
└─────────────────────────────────────────┘
```

## Data Source

- **Source**: https://www.amed.go.jp/koubo/saitaku_index.html
- **Coverage**: ~1,000+ research projects from 2015-2026
- **Update Frequency**: Manual/scheduled scraping

## Project Structure

```
amed-research-db/
├── scraper/           # Web scraping scripts
│   ├── scrape.py      # Main scraper
│   └── parser.py      # HTML parsing utilities
├── database/          # Database models and setup
│   ├── models.py      # SQLAlchemy models
│   └── init_db.py     # Database initialization
├── api/               # FastAPI application
│   ├── main.py        # FastAPI app entry point
│   ├── endpoints/     # API route handlers
│   └── analytics.py   # Analytics functions
├── tests/             # Test suite
├── data/              # Sample/test data
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Implementation Plan

### Phase 1: Data Collection (Week 1)
- [x] Project setup and planning
- [ ] Build scraper for main listing page
- [ ] Parse individual project pages
- [ ] Extract structured data
- [ ] Store raw HTML for backup
- [ ] Handle rate limiting and errors

### Phase 2: Database Design (Week 1-2)
- [ ] Design database schema
- [ ] Create SQLAlchemy models
- [ ] Set up migrations
- [ ] Import scraped data
- [ ] Add indexes for performance
- [ ] Data validation and cleaning

### Phase 3: API Development (Week 2-3)
- [ ] FastAPI application setup
- [ ] Core endpoints:
  - Search projects
  - Get project details
  - Statistics by year/institution/field
  - Trend analysis
  - Researcher profiles
  - Network analysis
- [ ] OpenAPI documentation
- [ ] Response formatting for LLM consumption
- [ ] Error handling

### Phase 4: Analytics Features (Week 3-4)
- [ ] Japanese text processing (MeCab)
- [ ] Keyword extraction
- [ ] Topic clustering
- [ ] Time series analysis
- [ ] Collaboration networks
- [ ] Institution rankings

### Phase 5: Testing & Deployment (Week 4)
- [ ] Unit tests
- [ ] Integration tests
- [ ] API documentation
- [ ] Docker containerization
- [ ] Deployment guide

## API Endpoints (Planned)

### Search & Retrieval
- `GET /api/projects/search` - Search projects with filters
- `GET /api/projects/{id}` - Get project details
- `GET /api/researchers/{name}` - Get researcher profile

### Statistics
- `GET /api/stats/overview` - Overall statistics
- `GET /api/stats/by_institution` - Projects by institution
- `GET /api/stats/by_field` - Projects by research field
- `GET /api/stats/by_year` - Projects by year

### Trends & Analysis
- `GET /api/trends/topics` - Topic trends over time
- `GET /api/trends/keywords` - Keyword frequency analysis
- `GET /api/trends/institutions` - Institution trends

### Network Analysis
- `GET /api/network/collaborations` - Collaboration networks
- `GET /api/network/institutions` - Institution relationships

## Data Schema (Planned)

### Projects
- id, title, description
- date, year, program_name
- field, category
- young_researcher_flag

### Researchers
- id, name, institution, position
- projects (relationship)

### Institutions
- id, name, location
- projects (relationship)

### Keywords
- id, keyword, frequency
- projects (relationship)

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run scraper
python scraper/scrape.py

# Initialize database
python database/init_db.py

# Run API server
uvicorn api.main:app --reload

# Access API docs
open http://localhost:8000/docs
```

## Usage Examples

### With Kiro-CLI
```bash
# Search for cancer research projects
kiro chat "Search AMED database for cancer research in 2024"

# Get institution statistics
kiro chat "Show me top 10 institutions by project count"

# Analyze trends
kiro chat "What are the emerging research topics in the last 3 years?"
```

### Direct API Calls
```bash
# Search projects
curl "http://localhost:8000/api/projects/search?q=がん&year=2024"

# Get statistics
curl "http://localhost:8000/api/stats/by_institution?top_n=10"
```

## Technology Stack

- **Language**: Python 3.10+
- **Web Framework**: FastAPI
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Scraping**: requests, BeautifulSoup4
- **Japanese NLP**: MeCab
- **Data Processing**: pandas
- **Testing**: pytest

## License

MIT

## Contributing

This is a personal project for research data analysis. Contributions welcome!
