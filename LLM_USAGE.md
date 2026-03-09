# LLM Usage Guide

## Overview

The AMED Research Database API is designed for LLM consumption. All endpoints return structured JSON that LLMs can easily parse and analyze.

## Quick Start for LLMs

**API Base URL:** `http://localhost:8000`

**Key Capabilities:**
- Search 30 research projects (sample data, 971 total available)
- Query by institution, researcher, program, year
- Get statistics and rankings
- Analyze trends

## Available Endpoints

### 1. Get Overview Statistics
```
GET /api/stats/overview
```
Returns total counts of projects, researchers, institutions, and programs.

**Example Response:**
```json
{
  "total_projects": 30,
  "total_researchers": 27,
  "total_institutions": 22,
  "total_programs": 3
}
```

### 2. Search Projects
```
GET /api/projects/search?q={query}&institution={name}&year={year}&limit={n}
```
Search projects with optional filters.

**Parameters:**
- `q`: Search term (searches title, researcher, institution)
- `institution`: Filter by institution name
- `researcher`: Filter by researcher name
- `program`: Filter by program name
- `year`: Filter by year (2025, 2026, etc.)
- `limit`: Max results (default 20, max 100)

**Example Response:**
```json
[
  {
    "id": 1,
    "title": "Fair Market Value に基づくタスクベース型費用算定の標準化...",
    "researcher": "田中 基嗣",
    "institution": "新潟大学",
    "position": "准教授",
    "program": "研究開発推進ネットワーク事業",
    "date": "2026-01-09"
  }
]
```

### 3. Get Project Details
```
GET /api/projects/{id}
```
Get full details of a specific project by ID.

### 4. Institution Rankings
```
GET /api/stats/by_institution?top_n={n}&year={year}
```
Get institutions ranked by project count.

**Example Response:**
```json
[
  {
    "name": "東京大学",
    "project_count": 2
  }
]
```

### 5. Year Statistics
```
GET /api/stats/by_year
```
Get project counts by year.

### 6. Researcher Profile
```
GET /api/researchers/{name}
```
Get researcher's profile and all their projects.

**Example Response:**
```json
{
  "name": "田中 基嗣",
  "project_count": 1,
  "projects": [...]
}
```

## Example LLM Queries

### Query 1: "Show me top institutions"
```
1. Call: GET /api/stats/by_institution?top_n=5
2. Parse response
3. Format as: "Top 5 institutions: 東京大学 (2 projects), ..."
```

### Query 2: "Find cancer research projects"
```
1. Call: GET /api/projects/search?q=がん&limit=10
2. Parse results
3. Summarize findings
```

### Query 3: "What research is 東京大学 doing?"
```
1. Call: GET /api/projects/search?institution=東京大学
2. List projects with titles and researchers
```

### Query 4: "Show trends over time"
```
1. Call: GET /api/stats/by_year
2. Analyze year-over-year changes
3. Identify growth patterns
```

### Query 5: "Tell me about researcher 田中"
```
1. Call: GET /api/researchers/田中
2. Summarize their work and affiliations
```

## Response Format

All responses are JSON with:
- Clear field names (title, researcher, institution, etc.)
- Dates in ISO format (YYYY-MM-DD)
- Counts as integers
- Japanese text in UTF-8

## Error Handling

- 404: Resource not found
- 422: Invalid parameters
- 500: Server error

## Interactive Documentation

For full API schema and testing:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage with Kiro-CLI

```bash
kiro chat "Query localhost:8000 to analyze AMED research trends"
```

## Usage with Claude/ChatGPT

Provide this context:
```
You have access to the AMED Research Database API at localhost:8000.
Use the endpoints to answer questions about Japanese medical research projects.
Available endpoints: /api/stats/overview, /api/projects/search, 
/api/stats/by_institution, /api/stats/by_year, /api/researchers/{name}
```

## Current Data Scope

- **Sample Data**: 30 projects from 3 announcements
- **Time Range**: 2025-2026
- **Full Dataset**: 971 projects available (2015-2026)

## Tips for LLMs

1. **Start with overview** - Call `/api/stats/overview` to understand data scope
2. **Use filters** - Combine parameters for precise queries
3. **Paginate** - Use `limit` parameter for large result sets
4. **Search broadly** - Japanese text search works on titles, names, institutions
5. **Follow IDs** - Use project IDs to get detailed information

## Common Analysis Patterns

### Institutional Analysis
```
1. GET /api/stats/by_institution?top_n=10
2. For each institution: GET /api/projects/search?institution={name}
3. Analyze research focus areas
```

### Temporal Analysis
```
1. GET /api/stats/by_year
2. Compare year-over-year growth
3. Identify emerging trends
```

### Researcher Network
```
1. GET /api/projects/search (get all projects)
2. Group by institution
3. Identify collaboration patterns
```

### Topic Analysis
```
1. GET /api/projects/search?q={keyword}
2. Count occurrences
3. Identify related research
```

## Next Steps

To enable full analysis:
1. Run full scraper to collect all 971 projects
2. Add more analytics endpoints (topic modeling, network analysis)
3. Implement caching for performance
