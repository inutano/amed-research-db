# LLM Quick Start

## For LLMs Using This API

**Base URL**: `http://localhost:8000`

### What You Can Do

1. **Get Statistics**: `/api/stats/overview`
2. **Search Projects**: `/api/projects/search?q={query}&limit=10`
3. **Institution Rankings**: `/api/stats/by_institution?top_n=5`
4. **Year Trends**: `/api/stats/by_year`
5. **Researcher Info**: `/api/researchers/{name}`

### Example Queries

**"Show me top institutions"**
→ `GET /api/stats/by_institution?top_n=5`

**"Find cancer research"**
→ `GET /api/projects/search?q=がん`

**"What's Tokyo University doing?"**
→ `GET /api/projects/search?institution=東京大学`

**"Show 2025 trends"**
→ `GET /api/projects/search?year=2025`

### Response Format

All responses are JSON with clear fields:
- `title`: Project title (Japanese)
- `researcher`: Researcher name
- `institution`: Institution name
- `program`: Program name
- `date`: Date (YYYY-MM-DD)

### Current Data

- 30 projects (sample)
- 27 researchers
- 22 institutions
- Years: 2025-2026

### Full Documentation

- Usage Guide: `LLM_USAGE.md`
- Enhancement Plan: `LLM_ENHANCEMENT_PLAN.md`
- API Docs: http://localhost:8000/docs

### Quick Test

```bash
curl http://localhost:8000/api/stats/overview
```

### For Kiro-CLI

```bash
kiro chat "Query localhost:8000 to show AMED research statistics"
```

---

**Ready to use!** Start querying to analyze Japanese medical research data.
