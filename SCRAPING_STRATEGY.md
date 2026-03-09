# Respectful Scraping Strategy

## Current Implementation

The production scraper (`scraper/scrape_all.py`) implements best practices for respectful web scraping:

### ✅ Rate Limiting
- **2-4 seconds delay** between requests (randomized)
- **~0.25-0.5 requests/second** (much slower than typical limits)
- **Random delays** to avoid appearing as automated traffic

### ✅ Proper Identification
- **User-Agent**: "AMED Research Database Bot (Academic Research)"
- Clearly identifies as a bot for academic purposes
- Includes Accept headers for proper content negotiation

### ✅ Error Handling
- **Max 3 retries** with 10-second delays
- **30-second timeout** per request
- Graceful failure handling (logs failed URLs)

### ✅ Progress Tracking
- **Saves progress every 50 pages**
- Can resume if interrupted
- Prevents re-scraping completed pages

### ✅ Resource Efficiency
- **Batch processing** to manage memory
- **Session reuse** for connection pooling
- Minimal server load

## Estimated Impact

**For 971 pages:**
- Time: ~45-80 minutes
- Rate: ~0.25-0.5 req/sec
- Total bandwidth: ~50-100 MB

**Comparison to typical traffic:**
- Human browsing: ~1-2 req/sec
- Our scraper: ~0.25-0.5 req/sec
- **50-75% slower than human**

## Additional Safety Measures

### 1. robots.txt Compliance
Check AMED's robots.txt:
```bash
curl https://www.amed.go.jp/robots.txt
```

### 2. Time-of-Day Consideration
Optional: Only scrape during business hours (9 AM - 6 PM JST)
- Reduces impact during peak usage
- Currently commented out but available

### 3. Monitoring
- Track request count and rate
- Log all errors
- Save failed URLs for manual review

## Running the Scraper

```bash
cd ~/repo/amed-research-db
python scraper/scrape_all.py
```

**What happens:**
1. Shows configuration
2. Asks for confirmation
3. Estimates time (~45-80 minutes)
4. Scrapes with 2-4s delays
5. Saves progress every 50 pages
6. Can be interrupted and resumed

## If Issues Arise

**If you get blocked:**
1. Stop immediately
2. Wait 24 hours
3. Increase delays (4-8 seconds)
4. Contact AMED to explain academic use

**If scraper fails:**
- Check `data/scraping_progress.json` for failed URLs
- Resume will skip completed pages
- Failed pages can be retried manually

## Ethical Considerations

✅ **Public data** - All pages are publicly accessible
✅ **Academic use** - For research analysis only
✅ **Respectful rate** - Much slower than human browsing
✅ **Proper identification** - Clear User-Agent
✅ **No circumvention** - No attempts to bypass restrictions
✅ **Minimal impact** - Low request rate, proper delays

## Alternative: Manual Collection

If concerned about automated scraping:
1. Use AMED's official database: https://amedfind.amed.go.jp/
2. Request bulk data from AMED directly
3. Scrape smaller batches (e.g., 100 pages/day)

## Recommendation

The current implementation is **very conservative** and should be safe:
- 2-4 second delays are generous
- Clear identification as academic bot
- Progress tracking prevents re-scraping
- Can be stopped/resumed anytime

**Suggested approach:**
1. Start with a small test (50 pages)
2. Monitor for any issues
3. If successful, continue with full scrape
4. Total time: ~1 hour for all 971 pages

This is significantly more respectful than typical web scraping practices.
