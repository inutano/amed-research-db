"""Tests for API endpoints."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from starlette.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


# --- Core endpoints ---

class TestRoot:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "AMED" in r.json()["message"]


class TestSearch:
    def test_search_no_params(self, client):
        r = client.get("/api/projects/search")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "projects" in data
        assert len(data["projects"]) <= 20  # default limit

    def test_search_with_query(self, client):
        r = client.get("/api/projects/search?q=がん&limit=5")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        assert len(data["projects"]) <= 5

    def test_search_by_year(self, client):
        r = client.get("/api/projects/search?year=2024&limit=5")
        assert r.status_code == 200
        data = r.json()
        for p in data["projects"]:
            assert p["date"] and "2024" in p["date"]

    def test_search_by_institution(self, client):
        r = client.get("/api/projects/search?institution=東京大学&limit=5")
        assert r.status_code == 200
        data = r.json()
        for p in data["projects"]:
            assert "東京大学" in (p["institution"] or "")

    def test_search_compact_format(self, client):
        r = client.get("/api/projects/search?q=がん&limit=3&format=compact")
        assert r.status_code == 200
        data = r.json()
        assert len(data["projects"]) > 0
        p = data["projects"][0]
        assert "by" in p
        assert "researcher" not in p
        assert "position" not in p

    def test_search_limit(self, client):
        r = client.get("/api/projects/search?limit=3")
        assert r.status_code == 200
        assert len(r.json()["projects"]) <= 3

    def test_search_returns_total(self, client):
        r = client.get("/api/projects/search?q=がん&limit=1")
        data = r.json()
        assert data["total"] > data["returned"]


class TestGetProject:
    def test_get_existing_project(self, client):
        # First get a project ID from search
        r = client.get("/api/projects/search?limit=1")
        projects = r.json()["projects"]
        if projects:
            pid = projects[0]["id"]
            r = client.get(f"/api/projects/{pid}")
            assert r.status_code == 200
            assert r.json()["id"] == pid

    def test_get_nonexistent_project(self, client):
        r = client.get("/api/projects/999999")
        assert r.status_code == 404


class TestStats:
    def test_overview(self, client):
        r = client.get("/api/stats/overview")
        assert r.status_code == 200
        data = r.json()
        assert data["total_projects"] > 0
        assert data["total_researchers"] > 0
        assert data["total_institutions"] > 0
        assert data["total_programs"] > 0

    def test_by_institution(self, client):
        r = client.get("/api/stats/by_institution?top_n=5")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 5
        # Should be sorted descending
        counts = [d["project_count"] for d in data]
        assert counts == sorted(counts, reverse=True)

    def test_by_institution_with_year(self, client):
        r = client.get("/api/stats/by_institution?top_n=3&year=2024")
        assert r.status_code == 200
        assert len(r.json()) <= 3

    def test_by_year(self, client):
        r = client.get("/api/stats/by_year")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        years = [d["year"] for d in data]
        assert years == sorted(years)


class TestResearcher:
    def test_get_researcher(self, client):
        # Search for a known researcher
        r = client.get("/api/projects/search?limit=1")
        projects = r.json()["projects"]
        if projects and projects[0].get("researcher"):
            name = projects[0]["researcher"]
            r = client.get(f"/api/researchers/{name}")
            assert r.status_code == 200
            assert r.json()["project_count"] > 0

    def test_nonexistent_researcher(self, client):
        r = client.get("/api/researchers/存在しない研究者名XYZ")
        assert r.status_code == 404


# --- LLM helper endpoints ---

class TestMetadata:
    def test_metadata(self, client):
        r = client.get("/api/metadata")
        assert r.status_code == 200
        data = r.json()
        assert "database" in data
        assert "filters" in data
        assert "endpoints" in data
        assert data["database"]["total_projects"] > 0
        assert len(data["filters"]["years"]) > 0
        assert len(data["filters"]["top_programs"]) > 0
        assert len(data["filters"]["top_institutions"]) > 0


class TestSuggestions:
    def test_suggestions(self, client):
        r = client.get("/api/suggestions")
        assert r.status_code == 200
        data = r.json()
        assert "examples" in data
        assert len(data["examples"]) > 5


class TestBulk:
    def test_bulk_query(self, client):
        r = client.post("/api/bulk", json={
            "queries": [
                {"path": "/api/stats/overview"},
                {"path": "/api/stats/by_year"},
            ]
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["results"]) == 2
        assert all(res["status"] == 200 for res in data["results"])

    def test_bulk_with_params(self, client):
        r = client.post("/api/bulk", json={
            "queries": [
                {"path": "/api/projects/search", "params": {"q": "がん", "limit": 2}},
            ]
        })
        assert r.status_code == 200
        assert r.json()["results"][0]["status"] == 200

    def test_bulk_max_limit(self, client):
        queries = [{"path": "/api/stats/overview"}] * 11
        r = client.post("/api/bulk", json={"queries": queries})
        assert r.status_code == 400


# --- Analytics endpoints ---

class TestAnalyticsTrends:
    def test_program_trends(self, client):
        r = client.get("/api/analytics/trends/programs?top_n=3")
        assert r.status_code == 200
        data = r.json()
        assert len(data["programs"]) == 3
        for p in data["programs"]:
            assert "name" in p
            assert "total" in p
            assert "by_year" in p
            assert p["total"] > 0

    def test_institution_trends(self, client):
        r = client.get("/api/analytics/trends/institutions?top_n=3")
        assert r.status_code == 200
        assert len(r.json()["institutions"]) == 3

    def test_program_trends_with_filter(self, client):
        r = client.get("/api/analytics/trends/programs?program=がん&top_n=3")
        assert r.status_code == 200
        for p in r.json()["programs"]:
            assert "がん" in p["name"]


class TestAnalyticsCompare:
    def test_compare_institutions(self, client):
        r = client.get("/api/analytics/compare?institutions=東京大学,京都大学")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "institution_comparison"
        assert len(data["entities"]) == 2

    def test_compare_programs(self, client):
        r = client.get("/api/analytics/compare?programs=がん医療,感染症")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "program_comparison"

    def test_compare_no_params(self, client):
        r = client.get("/api/analytics/compare")
        assert r.status_code == 400


class TestAnalyticsDetail:
    def test_program_detail(self, client):
        r = client.get("/api/analytics/programs/がん医療")
        assert r.status_code == 200
        data = r.json()
        assert data["total_projects"] > 0
        assert "by_year" in data
        assert "top_institutions" in data
        assert "top_researchers" in data

    def test_institution_detail(self, client):
        r = client.get("/api/analytics/institutions/東京大学")
        assert r.status_code == 200
        data = r.json()
        assert data["total_projects"] > 0

    def test_program_not_found(self, client):
        r = client.get("/api/analytics/programs/存在しないプログラムXYZ")
        assert r.status_code == 404

    def test_institution_not_found(self, client):
        r = client.get("/api/analytics/institutions/存在しない機関XYZ")
        assert r.status_code == 404


class TestAnalyticsYoungResearchers:
    def test_young_researchers(self, client):
        r = client.get("/api/analytics/young_researchers")
        assert r.status_code == 200
        data = r.json()
        assert "total_projects" in data
        assert "by_year" in data
        assert "top_institutions" in data


class TestAnalyticsKeywords:
    def test_keyword_search(self, client):
        r = client.get("/api/analytics/keyword_search?keywords=AI,がん")
        assert r.status_code == 200
        data = r.json()
        assert "AI" in data["keywords"]
        assert "がん" in data["keywords"]
        assert data["keywords"]["がん"]["total"] > 0

    def test_keyword_no_params(self, client):
        r = client.get("/api/analytics/keyword_search?keywords=")
        assert r.status_code == 400


class TestAnalyticsCollaborations:
    def test_collaborations_by_institution(self, client):
        r = client.get("/api/analytics/collaborations?institution=東京大学&top_n=5")
        assert r.status_code == 200
        data = r.json()
        assert "co_institutions" in data
        assert len(data["co_institutions"]) <= 5

    def test_collaborations_by_program(self, client):
        r = client.get("/api/analytics/collaborations?program=がん医療&top_n=5")
        assert r.status_code == 200
        assert "participating_institutions" in r.json()

    def test_collaborations_no_params(self, client):
        r = client.get("/api/analytics/collaborations")
        assert r.status_code == 400
