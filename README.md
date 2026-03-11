# AMED Research Database

A searchable database and API for research proposals accepted by [AMED](https://www.amed.go.jp/) (Japan Agency for Medical Research and Development), designed for analysis by humans and LLMs alike.

## What's Inside

- **~3,800 projects** from 2015-2025, scraped from [AMED's public listings](https://www.amed.go.jp/koubo/saitaku_index.html)
- **3,000+ researchers**, **700+ institutions**, **200+ programs**
- Pre-built SQLite database included (`database/amed.db`) - ready to query immediately
- REST API with search, analytics, and LLM-optimized endpoints
- MCP server for direct integration with Claude and other LLM tools
- [PDF summary report](AMED_Report.pdf) with charts and analysis

## Quick Start

```bash
pip install -r requirements.txt

# Start the API server
uvicorn api.main:app --reload
# → http://localhost:8000/docs

# Or use the MCP server with Claude
python mcp_server.py
```

### Docker

```bash
docker compose up
# → http://localhost:8000/docs
```

## API Endpoints

### Search
- `GET /api/projects/search?q=がん&year=2024` - Search projects (supports `format=compact`)
- `POST /api/projects/bulk` - Bulk query multiple searches

### Statistics
- `GET /api/stats` - Overview statistics
- `GET /api/metadata` - Database metadata for LLM context
- `GET /api/suggestions` - Suggested queries

### Analytics (`/api/analytics/`)
- `trends/by-year` - Project count trends
- `trends/keywords?keywords=AI,がん,ゲノム` - Keyword frequency over time
- `institutions/top?top_n=15` - Top institutions
- `institutions/compare?names=東京大学,京都大学` - Side-by-side comparison
- `institutions/collaborators?institution=東京大学` - Co-participating institutions
- `programs/top` - Top research programs
- `researchers/profile?name=田中` - Researcher lookup
- `researchers/young-ratio` - Young researcher program stats

## MCP Server

For use with Claude Code, Claude Desktop, or any MCP-compatible client:

```json
{
  "mcpServers": {
    "amed": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/amed-research-db"
    }
  }
}
```

Tools: `search_projects`, `get_stats`, `top_institutions`, `compare_institutions`, `keyword_trends`, `researcher_profile`, `find_collaborators`

## Project Structure

```
amed-research-db/
├── api/
│   ├── main.py          # FastAPI app with search, stats, metadata
│   └── analytics.py     # Analytics endpoints (trends, comparisons)
├── database/
│   ├── models.py        # SQLAlchemy models (Project, Researcher, etc.)
│   ├── import_all.py    # Batch data importer
│   └── amed.db          # Pre-built SQLite database
├── scraper/
│   ├── scrape.py        # Link collector
│   ├── scrape_all.py    # Full scraper with progress tracking
│   └── parser.py        # HTML parser (header-based column detection)
├── tests/               # 65 tests (parser + API)
├── mcp_server.py        # MCP server for LLM integration
├── AMED_Report.pdf      # Summary report with charts
├── Dockerfile
└── docker-compose.yml
```

## Rebuilding the Database

If you want to re-scrape and rebuild from scratch:

```bash
# 1. Scrape project links
python scraper/scrape.py

# 2. Scrape all project pages (takes ~30 min, respectful rate limiting)
python scraper/scrape_all.py

# 3. Import into database
python database/import_all.py
```

## Tech Stack

- Python 3.10+, FastAPI, SQLAlchemy, SQLite
- BeautifulSoup4 (scraping), pytest (testing)
- MCP (Model Context Protocol) for LLM integration
- reportlab + matplotlib (PDF report)

## Data Source

All data is from AMED's publicly available accepted proposal listings at https://www.amed.go.jp/koubo/saitaku_index.html

## License

MIT
