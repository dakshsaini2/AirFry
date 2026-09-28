# APIx - Real-time Airfare Price Index (SIH)
Run locally: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn backend.app:app --reload` -> http://localhost:8000 (docs at /docs). Tests: `pytest -q`.
Deploy: Render (API + UI) via render.yaml; Vercel (UI) - set the Render URL in vercel.json rewrites.
