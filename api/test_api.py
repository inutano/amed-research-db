"""Test API endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*60)
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
        if len(json.dumps(data)) > 500:
            print("... (truncated)")
    except Exception as e:
        print(f"Error: {e}")

# Test all endpoints
test_endpoint("Root", f"{BASE_URL}/")
test_endpoint("Overview Stats", f"{BASE_URL}/api/stats/overview")
test_endpoint("Search Projects", f"{BASE_URL}/api/projects/search?limit=3")
test_endpoint("Search by Institution", f"{BASE_URL}/api/projects/search?institution=東京大学")
test_endpoint("Institution Stats", f"{BASE_URL}/api/stats/by_institution?top_n=5")
test_endpoint("Year Stats", f"{BASE_URL}/api/stats/by_year")
test_endpoint("Get Project", f"{BASE_URL}/api/projects/1")
test_endpoint("Get Researcher", f"{BASE_URL}/api/researchers/田中")

print("\n" + "="*60)
print("All tests completed!")
print("="*60)
