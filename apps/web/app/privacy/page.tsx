import Link from "next/link";

export const metadata = {
  title: "Privacy Policy — VelaMed",
  description: "How VelaMed handles the information you enter.",
};

export default function Privacy() {
  return (
    <>
      <header className="top">
        <div className="wrap">
          <Link href="/" style={{ textDecoration: "none" }}>
            <span className="brand">VelaMed<span>by Sitelytc</span></span>
          </Link>
        </div>
      </header>

      <main className="wrap" style={{ paddingBottom: 48 }}>
        <h1 style={{ fontSize: 28, marginTop: 24 }}>Privacy Policy</h1>
        <p style={{ color: "var(--grey)" }}>Last updated: 16 November 2026</p>

        <h2 style={{ fontSize: 18, marginTop: 24 }}>Who we are</h2>
        <p>
          VelaMed is a service of Sitelytc Digital Media Pvt. Ltd., Nihal Vihar, New Delhi.
          For any question or request about your data, contact our grievance officer at{" "}
          <a href="mailto:privacy@sitelytc.com">privacy@sitelytc.com</a>.
        </p>

        <h2 style={{ fontSize: 18, marginTop: 24 }}>What we collect, and why</h2>
        <p>
          We collect the following information only for the purpose of providing the check you
          requested and sending you the report — nothing else.
        </p>
        <ul>
          <li>
            <strong>The website address you enter</strong> — used only to run a one-time passive
            check of that public website. We do not log in to it, scan it, or probe it.
          </li>
          <li>
            <strong>Your email address</strong>, if you choose to enter it to receive the report —
            used only to send you that report and, where you have agreed, occasional related
            updates. You can ask us to delete it at any time.
          </li>
        </ul>
        <p>
          We do not use advertising trackers or third-party analytics cookies on this site.
        </p>

        <h2 style={{ fontSize: 18, marginTop: 24 }}>Retention</h2>
        <p>
          Scan results are kept only as long as needed to show you the report. Email addresses are
          kept until you ask us to remove them.
        </p>

        <h2 style={{ fontSize: 18, marginTop: 24 }}>Your rights</h2>
        <p>
          You can ask us to access, correct, or delete the information you have given us. Email{" "}
          <a href="mailto:privacy@sitelytc.com">privacy@sitelytc.com</a> and we will act on it.
        </p>

        <p style={{ marginTop: 28 }}>
          <Link href="/">← Back to VelaMed</Link>
        </p>
      </main>
    </>
  );
}
