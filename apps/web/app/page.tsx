"use client";

import { useState } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "https://velamed-api.onrender.com";

type Check = { pass: boolean | null; detail: string };
type Item = { key: string; group: string; label: string; points: number; max: number; note: string };
type ScanResult = {
  id: string;
  host: string;
  score: number;
  max: number;
  band: string;
  scoring: { items: Item[]; colour: string };
  checks: Record<string, Check>;
};

const bandColour = (band: string) =>
  band === "Good" ? "var(--good)" : band === "Needs attention" ? "var(--warn)" : "var(--risk)";

function Mark({ points, max }: { points: number; max: number }) {
  if (points === max) return <span className="m" style={{ color: "var(--good)" }}>✓</span>;
  if (points === 0) return <span className="m" style={{ color: "var(--risk)" }}>✕</span>;
  return <span className="m" style={{ color: "var(--warn)" }}>!</span>;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [email, setEmail] = useState("");
  const [emailDone, setEmailDone] = useState(false);

  async function scan(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    setEmailDone(false);
    try {
      const res = await fetch(`${API}/scan`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Scan failed (${res.status})`);
      }
      setResult(await res.json());
    } catch (err: any) {
      setError(err.message || "Something went wrong. The free service may be waking up — try again.");
    } finally {
      setLoading(false);
    }
  }

  async function submitEmail(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !result) return;
    // Persist the lead (best-effort) — never block the report on it.
    try {
      await fetch(`${API}/lead`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          scan_id: result.id,
          host: result.host,
          score: result.score,
          max: result.max,
          band: result.band,
        }),
      });
    } catch {
      /* ignore — show the report regardless */
    }
    setEmailDone(true);
  }

  const groups = result ? Array.from(new Set(result.scoring.items.map((i) => i.group))) : [];

  return (
    <>
      <header className="top">
        <div className="wrap">
          <span className="brand">VelaMed<span>by Sitelytc</span></span>
        </div>
      </header>

      <main className="wrap">
        <section className="hero">
          <h1>Is your hospital&apos;s website DPDP-ready?</h1>
          <p>
            A free, passive check of your website and patient portal for DPDP readiness and basic
            security — in under a minute. India&apos;s data-protection rules are enforceable from{" "}
            <span className="deadline">13 May 2027</span>.
          </p>
        </section>

        <form className="scan" onSubmit={scan}>
          <input
            type="text"
            placeholder="yourhospital.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            aria-label="Website URL"
          />
          <button type="submit" disabled={loading}>
            {loading ? "Checking…" : "Check now"}
          </button>
        </form>
        <div className="hint">We only look at what any visitor&apos;s browser sees. No scanning, no login.</div>
        {error && <div className="err">{error}</div>}

        {result && (
          <div className="card">
            <div className="scorehead">
              <div className="host">{result.host}</div>
              <div className="scorebox">
                <div className="n" style={{ color: bandColour(result.band) }}>
                  {result.score}<span style={{ fontSize: 16, color: "var(--grey)" }}>/{result.max}</span>
                </div>
                <div className="b" style={{ color: bandColour(result.band) }}>{result.band}</div>
              </div>
            </div>

            {groups.map((g) => {
              const items = result.scoring.items.filter((i) => i.group === g);
              const gp = items.reduce((s, i) => s + i.points, 0);
              const gm = items.reduce((s, i) => s + i.max, 0);
              return (
                <div key={g}>
                  <div className="grp"><span>{g}</span><span>{gp}/{gm}</span></div>
                  {items.map((i) => (
                    <div className="row" key={i.key}>
                      <Mark points={i.points} max={i.max} />
                      <div>
                        <span className="lbl">{i.label}</span>
                        <span className="note">{i.note}</span>
                      </div>
                      <div className="pts">{i.points}/{i.max}</div>
                    </div>
                  ))}
                </div>
              );
            })}

            <div className="lead">
              <h3>Get the full one-page report (PDF)</h3>
              {!emailDone ? (
                <form onSubmit={submitEmail}>
                  <input
                    type="email"
                    required
                    placeholder="you@hospital.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    aria-label="Email"
                  />
                  <button type="submit">Email me the report</button>
                </form>
              ) : null}
              {!emailDone && (
                <p className="disclaimer" style={{ marginTop: 8 }}>
                  We use your email only to send this report. See our{" "}
                  <Link href="/privacy">Privacy Policy</Link>.
                </p>
              )}
              {emailDone && (
                <a className="btn" href={`${API}/scan/${result.id}/report.pdf`} target="_blank" rel="noreferrer">
                  Download the PDF report
                </a>
              )}
            </div>

            <p className="disclaimer">
              This is a passive review of your public surface. The points above are gaps to review,
              not a legal determination of DPDP compliance.
            </p>
          </div>
        )}
      </main>

      <footer className="foot">
        VelaMed — a Sitelytc Digital Media Pvt. Ltd. service. Passive checks only.
        <br />
        <Link href="/privacy">Privacy Policy</Link>
      </footer>
    </>
  );
}
