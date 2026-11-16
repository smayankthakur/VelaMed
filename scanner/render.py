"""
Optional JS rendering (Playwright) — for pages whose forms load via JavaScript.

Still passive: this loads the page exactly as a visitor's browser would, waits
for it to settle, and reads the resulting DOM. No interaction, no submission.

Playwright is optional. If it (or its browser) isn't installed, render_html
raises RenderUnavailable and the caller falls back to static HTML.

    pip install playwright
    playwright install chromium
"""


class RenderUnavailable(RuntimeError):
    pass


def render_html(url: str, timeout: int = 15) -> str:
    """Load the page in headless Chromium and return the rendered HTML."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RenderUnavailable("playwright not installed (pip install playwright)") from e

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            try:
                page = browser.new_page(user_agent="VelaMed-PassiveScanner/0.1")
                page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
                return page.content()
            finally:
                browser.close()
    except RenderUnavailable:
        raise
    except Exception as e:
        # Browser missing, launch failure, nav timeout, etc. — treat as unavailable.
        raise RenderUnavailable(f"{e.__class__.__name__}: {e}") from e
