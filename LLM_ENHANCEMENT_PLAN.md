# LLM-First Enhancement Plan

## Current State

✅ **Working**: RESTful API with JSON responses
✅ **LLM-Ready**: Structured data, clear field names
✅ **Documented**: OpenAPI schema auto-generated

## Enhancement Roadmap

### Phase 1: Natural Language Query Interface (Week 1)

**Goal**: Allow LLMs to query using natural language descriptions

**Implementation**:
```
POST /api/query
{
  "question": "What are the top institutions in cancer research?"
}
```

**Features**:
- Parse natural language intent
- Map to appropriate API calls
- Return structured results + natural language summary
- Support multi-step queries

**Tech Stack**:
- LangChain for query parsing
- Function calling / tool use
- Response formatting

### Phase 2: Conversational Context (Week 2)

**Goal**: Support multi-turn conversations with context

**Implementation**:
```
POST /api/chat
{
  "session_id": "abc123",
  "message": "Show me more about the first institution"
}
```

**Features**:
- Session management
- Context tracking (previous queries, results)
- Follow-up question handling
- Reference resolution ("the first one", "that researcher")

**Tech Stack**:
- Redis for session storage
- Context window management
- Conversation history

### Phase 3: Advanced Analytics Endpoints (Week 3)

**Goal**: Pre-computed analytics for common LLM queries

**New Endpoints**:

1. **Topic Clustering**
   ```
   GET /api/analytics/topics?year=2025
   ```
   Returns: Top research topics with project counts

2. **Collaboration Networks**
   ```
   GET /api/analytics/collaborations?institution={name}
   ```
   Returns: Co-investigator networks, institutional partnerships

3. **Trend Analysis**
   ```
   GET /api/analytics/trends?topic={keyword}&years=2020-2025
   ```
   Returns: Time series data, growth rates, predictions

4. **Researcher Profiles (Enhanced)**
   ```
   GET /api/analytics/researcher/{name}/profile
   ```
   Returns: Career trajectory, collaboration patterns, research evolution

5. **Comparative Analysis**
   ```
   POST /api/analytics/compare
   {
     "entities": ["東京大学", "京都大学"],
     "metrics": ["project_count", "research_areas"]
   }
   ```

**Tech Stack**:
- pandas for data analysis
- NetworkX for network analysis
- scikit-learn for clustering
- Pre-computed caches

### Phase 4: Semantic Search (Week 4)

**Goal**: Enable semantic similarity search beyond keyword matching

**Implementation**:
```
POST /api/search/semantic
{
  "query": "research on using AI for drug discovery",
  "limit": 10
}
```

**Features**:
- Embed project titles/descriptions using Japanese BERT
- Vector similarity search
- Cross-lingual search (English → Japanese)
- Related project recommendations

**Tech Stack**:
- sentence-transformers (Japanese models)
- FAISS or ChromaDB for vector storage
- cl-tohoku/bert-base-japanese

### Phase 5: LLM Function Calling Integration (Week 5)

**Goal**: Native integration with LLM function calling

**Implementation**:

Create OpenAI-compatible function definitions:
```json
{
  "name": "search_amed_projects",
  "description": "Search AMED research projects",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "institution": {"type": "string"},
      "year": {"type": "integer"}
    }
  }
}
```

**Features**:
- Auto-generate function schemas from API
- Provide example calls
- Return formatted responses
- Support Claude MCP protocol

**Tech Stack**:
- OpenAPI → Function schema converter
- MCP server implementation
- Streaming responses

### Phase 6: Intelligent Caching & Optimization (Week 6)

**Goal**: Fast responses for LLM queries

**Features**:
- Cache common queries
- Pre-compute aggregations
- Materialized views for statistics
- Query result caching with TTL
- Rate limiting per session

**Tech Stack**:
- Redis for caching
- PostgreSQL materialized views
- Query optimization

## Quick Wins (Immediate)

### 1. Add Query Suggestions Endpoint
```
GET /api/suggestions
```
Returns common query patterns LLMs can use.

### 2. Add Bulk Query Endpoint
```
POST /api/bulk
{
  "queries": [
    {"endpoint": "/api/stats/overview"},
    {"endpoint": "/api/projects/search", "params": {"limit": 5}}
  ]
}
```
Reduces round trips for complex analyses.

### 3. Add Response Formatting Options
```
GET /api/projects/search?format=summary
```
Returns condensed data optimized for LLM context windows.

### 4. Add Metadata Endpoint
```
GET /api/metadata
```
Returns data schema, available filters, value ranges for LLM planning.

## Implementation Priority

**High Priority** (Do First):
1. ✅ Basic REST API (DONE)
2. Bulk query endpoint
3. Response formatting options
4. Query suggestions

**Medium Priority** (Next):
5. Natural language query interface
6. Advanced analytics endpoints
7. Semantic search

**Low Priority** (Later):
8. Conversational context
9. Function calling integration
10. Intelligent caching

## Minimal LLM-First Additions (This Week)

### Add to existing API:

1. **Bulk Query Endpoint** (30 min)
   - Single request, multiple queries
   - Reduces latency for complex analysis

2. **Query Suggestions** (15 min)
   - List of example queries
   - Helps LLMs understand capabilities

3. **Condensed Response Format** (20 min)
   - `?format=compact` parameter
   - Smaller responses for context efficiency

4. **Metadata Endpoint** (15 min)
   - Schema information
   - Available filters and values
   - Helps LLMs construct valid queries

**Total Time**: ~1.5 hours for immediate LLM improvements

## Long-term Vision

**Goal**: LLM can autonomously:
1. Understand research questions
2. Query the database efficiently
3. Perform multi-step analysis
4. Generate insights and visualizations
5. Answer follow-up questions with context

**Example Flow**:
```
User: "Compare cancer research trends between Tokyo and Kyoto universities"

LLM:
1. Calls /api/projects/search?q=がん&institution=東京大学
2. Calls /api/projects/search?q=がん&institution=京都大学
3. Calls /api/analytics/trends for both
4. Synthesizes comparison
5. Generates summary with key findings
```

## Success Metrics

- Query response time < 200ms
- LLM can answer 90% of research questions
- Multi-step analysis without human intervention
- Context window usage < 50% for typical queries
- Zero-shot query success rate > 80%

## Next Steps

1. Implement quick wins (bulk query, suggestions, formatting)
2. Test with Kiro-CLI for real usage patterns
3. Collect query logs to identify common patterns
4. Prioritize analytics endpoints based on usage
5. Iterate based on LLM feedback
