# VelaMed API

A thin FastAPI wrapper over the passive scanner. Passive only.

## Run

```bash
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs for the interactive API docs.

## Endpoints

| Method | Path                      | Does                                   |
| ------ | ------------------------- | -------------------------------------- |
| GET    | `/health`                 | liveness check                         |
| POST   | `/scan`                   | `{"url": "..."}` → score + checks JSON |
| GET    | `/scan/{id}`              | retrieve a stored scan                 |
| GET    | `/scan/{id}/report.html`  | one-page HTML report                   |
| GET    | `/scan/{id}/report.pdf`   | one-page PDF report                    |

Example:

```bash
curl -s -X POST localhost:8000/scan -H 'content-type: application/json' \
  -d '{"url":"example.com"}' | python3 -m json.tool
```

## Notes

- Scans are held in an in-memory store for now — they vanish on restart.
  A database (Supabase/Postgres) lands in M5/M6, along with lead capture.
- `allow_origins` is `*` for development; restrict it to your front-end
  domain before production.
- The API inherits the scanner's rule: **passive only.** The paid active
  (VAPT) tier is a separate, ownership-gated service, not this endpoint.
