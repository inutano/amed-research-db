# API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### General

#### `GET /`
Root endpoint with API information.

**Response:**
```json
{
  "message": "AMED Research Database API",
  "docs": "/docs",
  "version": "0.1.0"
}
```

### Projects

#### `GET /api/projects/search`
Search projects with filters.

**Query Parameters:**
- `q` (string, optional): Search query (searches title, researcher, institution)
- `year` (int, optional): Filter by year
- `institution` (string, optional): Filter by institution name
- `researcher` (string, optional): Filter by researcher name
- `program` (string, optional): Filter by program name
- `limit` (int, default=20, max=100): Maximum results

**Example:**
```bash
curl "http://localhost:8000/api/projects/search?institution=東京大学&limit=5"
```

**Response:**
```json
[
  {
    "id": 2,
    "title": "患者・市民参画に基づく治験・臨床試験レイサマリーの普及促進に関する研究",
    "researcher": "武藤 香織",
    "institution": "東京大学",
    "position": "教授",
    "program": "研究開発推進ネットワーク事業",
    "date": "2026-01-09"
  }
]
```

#### `GET /api/projects/{project_id}`
Get project details by ID.

**Example:**
```bash
curl "http://localhost:8000/api/projects/1"
```

### Statistics

#### `GET /api/stats/overview`
Get overall database statistics.

**Response:**
```json
{
  "total_projects": 30,
  "total_researchers": 27,
  "total_institutions": 22,
  "total_programs": 3
}
```

#### `GET /api/stats/by_institution`
Get project counts by institution.

**Query Parameters:**
- `top_n` (int, default=10, max=100): Number of top institutions
- `year` (int, optional): Filter by year

**Example:**
```bash
curl "http://localhost:8000/api/stats/by_institution?top_n=5"
```

**Response:**
```json
[
  {
    "name": "東京大学",
    "project_count": 2
  }
]
```

#### `GET /api/stats/by_year`
Get project counts by year.

**Response:**
```json
[
  {
    "year": 2025,
    "project_count": 28
  },
  {
    "year": 2026,
    "project_count": 2
  }
]
```

### Researchers

#### `GET /api/researchers/{name}`
Get researcher profile and projects.

**Example:**
```bash
curl "http://localhost:8000/api/researchers/田中"
```

**Response:**
```json
{
  "name": "田中 基嗣",
  "project_count": 1,
  "projects": [
    {
      "title": "Fair Market Value に基づくタスクベース型費用算定の標準化と実装評価...",
      "institution": "新潟大学",
      "program": "研究開発推進ネットワーク事業",
      "date": "2026-01-09"
    }
  ]
}
```

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage with Kiro-CLI

```bash
# Start the API
./start_api.sh

# In another terminal, use Kiro-CLI
kiro chat "Query the AMED API at localhost:8000 to find cancer research projects from 2024"
```

## Example Queries for LLM

1. "Show me all projects from 東京大学"
2. "What are the top 5 institutions by project count?"
3. "Find projects related to cancer research"
4. "Get statistics for 2025"
5. "Show me all projects by researcher 田中"
