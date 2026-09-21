# AMED Research Database

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22882293.svg)](https://doi.org/10.5281/zenodo.22882293)

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
```

The MCP server needs a separate environment, because `mcp` requires newer
starlette and pydantic releases than the API stack pins:

```bash
pip install -r requirements-mcp.txt
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

For use with Claude Code, Claude Desktop, or any MCP-compatible client.
Install `requirements-mcp.txt` first (see Quick Start), then:

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
│   ├── scrape_all.py    # Full scraper: link collection + progress tracking
│   ├── parser.py        # HTML parser (header-based column detection)
│   ├── check_new.py     # Detect newly published announcements
│   └── find_missing.py  # Re-scrape pages missing from the database
├── tests/               # 65 tests (parser + API)
├── mcp_server.py        # MCP server for LLM integration
├── requirements.txt     # API, scraper, tests
├── requirements-mcp.txt # MCP server (separate environment)
├── AMED_Report.pdf      # Summary report with charts
├── Dockerfile
└── docker-compose.yml
```

## Rebuilding the Database

If you want to re-scrape and rebuild from scratch:

```bash
# 1. Collect links and scrape all project pages
#    (takes ~30 min, respectful rate limiting; resumes from saved progress)
python scraper/scrape_all.py

# 2. Import into database
python database/import_all.py
```

## Tech Stack

- Python 3.10+, FastAPI, SQLAlchemy, SQLite
- BeautifulSoup4 (scraping), pytest (testing)
- MCP (Model Context Protocol) for LLM integration
- reportlab + matplotlib (PDF report)

## Data Source

All data is from AMED's publicly available accepted proposal listings at https://www.amed.go.jp/koubo/saitaku_index.html

## Citation

Each release is archived on Zenodo. Cite the concept DOI
[10.5281/zenodo.22882293](https://doi.org/10.5281/zenodo.22882293), which
always resolves to the latest version, or the DOI of the specific version you
used (v1.0.0 is
[10.5281/zenodo.22882294](https://doi.org/10.5281/zenodo.22882294)).

> Ohta, T. (2026). *AMED Research Database: a searchable database, REST API,
> and MCP server for AMED-funded research projects* (v1.0.0) [Software].
> Zenodo. https://doi.org/10.5281/zenodo.22882293

See `CITATION.cff`, or GitHub's "Cite this repository" button, for a
machine-readable version.

## License

- **Code** — MIT (`LICENSE`)
- **Data and report** — CC BY 4.0: `database/amed.db` and `AMED_Report.pdf` (`LICENSE-DATA`)

The CC BY 4.0 terms cover the compilation and the derived analyses, not the
upstream listings themselves. Check AMED's own terms of use before
redistributing the source material.
