# VelaMed — web front end (M5)

Next.js (App Router) front end for the passive scanner. A visitor enters a URL,
gets a 0–40 score with the Security / DPDP breakdown, and can request the
one-page PDF report. Calls the VelaMed API.

## Run locally

```bash
cd apps/web
npm install
cp .env.example .env.local      # points at the live API by default
npm run dev                     # http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local` to use a local
API (`apps/api`) instead of the deployed one.

## Deploy (M6)

Deploys to Vercel as-is. Set the project root to `apps/web` and add the
environment variable `NEXT_PUBLIC_API_URL` pointing at the Render API
(`https://velamed-api.onrender.com`).

## Notes

- Email capture currently reveals the report link client-side; wiring it to
  storage (a lead record) lands in M6 with the database.
- The UI mirrors the PDF report: Security (24) and DPDP (16), grouped with
  subtotals, framed as "gaps to review".
