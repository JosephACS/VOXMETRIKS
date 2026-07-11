"""HTTP endpoint smoke test."""
import json
import urllib.request

BASE = "http://127.0.0.1:8001"
ENDPOINTS = [
    "/health",
    "/artists/growth",
    "/artists/top?limit=2",
    "/streams/daily?days=3",
    "/streams/engagement",
    "/genres/trends?limit=2",
    "/genres/popularity?limit=2",
    "/recommendations/tracks?limit=2",
    "/users/segments",
    "/users/retention",
    "/audit/pipeline",
    "/audit/data-quality",
]

for path in ENDPOINTS:
    body = json.loads(urllib.request.urlopen(BASE + path).read())
    assert body["status"] == "success", path
    assert "data" in body and "message" in body
    if path != "/health":
        assert "insight" in body["data"]
    print("OK", path)

print("All route checks passed.")
