# Quick Start Guide

## Start the API

```bash
cd /Users/inutano/amed-research-db
./start_api.sh
```

The API will be available at: http://localhost:8000

## Test the API

```bash
# Get overview stats
curl http://localhost:8000/api/stats/overview

# Search projects
curl "http://localhost:8000/api/projects/search?limit=5"

# Search by institution
curl "http://localhost:8000/api/projects/search?institution=東京大学"

# Get top institutions
curl "http://localhost:8000/api/stats/by_institution?top_n=5"
```

## Use with Kiro-CLI

Start the API in one terminal, then in another:

```bash
kiro chat "Query the AMED API at localhost:8000 to find all projects from 東京大学"
```

## View Documentation

Open in browser:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Current Data

- 30 projects (sample data)
- 27 researchers
- 22 institutions
- 3 programs

Full dataset (971 projects) can be collected by running the full scraper.
