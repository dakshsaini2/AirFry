import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://127.0.0.1:8000"

endpoints = [
    "/api/v1/health",
    "/api/v1/methodology",
    "/api/v1/summary",
    "/api/v1/index?freq=D",
    "/api/v1/elasticity?route=DEL-BOM",
    "/api/v1/heatmap",
    "/api/v1/carriers",
    "/api/v1/fares?limit=5",
    "/api/v1/backtest",
    "/api/v1/validation_report"
]

print("Starting API Check...\n")

all_passed = True
for ep in endpoints:
    url = f"{BASE_URL}{ep}"
    try:
        start_time = time.time()
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read()
            elapsed = (time.time() - start_time) * 1000
            if status == 200:
                print(f"[OK] {ep} ({elapsed:.0f}ms)")
            else:
                print(f"[FAIL] {ep} (Status: {status})")
                all_passed = False
    except urllib.error.URLError as e:
        print(f"[ERROR] {ep} - {e}")
        all_passed = False

if all_passed:
    print("\n✅ All GET endpoints responded successfully with 200 OK.")
else:
    print("\n❌ Some endpoints failed.")
