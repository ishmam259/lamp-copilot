"""Export the technical documentation and the security self-assessment to PDF.

    pip install markdown playwright
    python docs/technical/build_pdfs.py

Renders each Markdown file to HTML with the deck's colours and prints it with
Microsoft Edge (Playwright, channel "msedge"). Pass --chromium to use Playwright's
own Chromium instead (run `playwright install chromium` once).
"""

import base64
import re
import sys
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parents[1]
FILES = [
    DOCS / "technical" / "TECHNICAL_DOCUMENTATION.md",
    DOCS / "security" / "SECURITY_SELF_ASSESSMENT.md",
]

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
:root { --deep: #0F5132; --mid: #198754; --bright: #00BF63; --mint: #E9F7EE; --ink: #231F20; --grey: #555; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; line-height: 1.5; color: var(--ink); }
h1, h2, h3 { font-family: "Poppins SemiBold", "Poppins", "Segoe UI", sans-serif; font-weight: 600; color: var(--deep); }
h1 { font-size: 24pt; margin: 0 0 4pt; line-height: 1.2; }
h1 + p { font-size: 13pt; color: var(--mid); margin-top: 0; }
h2 { font-size: 15pt; margin: 22pt 0 8pt; padding-bottom: 4pt; border-bottom: 2px solid var(--bright); break-after: avoid; }
h3 { font-size: 11.5pt; margin: 14pt 0 6pt; color: var(--mid); break-after: avoid; }
hr { border: 0; border-top: 1px solid #ddd; margin: 14pt 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9pt; break-inside: auto; }
tr { break-inside: avoid; }
th { background: var(--deep); color: #fff; text-align: left; padding: 5pt 6pt; font-weight: 600; }
td { padding: 4pt 6pt; border-bottom: 1px solid #dfe7e2; vertical-align: top; }
tr:nth-child(even) td { background: var(--mint); }
code { font-family: Consolas, "Courier New", monospace; font-size: 8.8pt; background: #f1f4f2; padding: 0 2pt; border-radius: 2px; }
pre { background: #f6f8f7; border-left: 3px solid var(--bright); padding: 8pt 10pt; font-size: 8.2pt; line-height: 1.35;
      white-space: pre; overflow: hidden; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: inherit; }
strong { color: #000; }
ul, ol { padding-left: 18pt; }
li { margin: 1pt 0; }
figure { margin: 10pt 0 12pt; break-inside: avoid; }
figure img { width: 100%; display: block; }
figcaption { font-size: 8.6pt; color: var(--grey); margin-top: 5pt; line-height: 1.4; }
"""

FOOTER = ('<div style="font-size:7.5pt;color:#777;width:100%;padding:0 16mm;display:flex;justify-content:space-between;'
          'font-family:Segoe UI,Arial,sans-serif"><span>LaMP-Copilot · Team LaMP · FinTechathon 2026</span>'
          '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')


def render(page, md_path: Path) -> Path:
    body = markdown.markdown(md_path.read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists"])
    # Images are inlined: set_content has no base URL, so relative paths would not load.
    body = re.sub(r'src="([^":]+\.png)"', lambda m: 'src="data:image/png;base64,'
                  + base64.b64encode((md_path.parent / m.group(1)).read_bytes()).decode() + '"', body)
    html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{md_path.stem}</title>' \
           f"<style>{CSS}</style></head><body>{body}</body></html>"
    page.set_content(html, wait_until="load")
    out = md_path.with_suffix(".pdf")
    page.pdf(path=str(out), format="A4", print_background=True, display_header_footer=True,
             header_template="<div></div>", footer_template=FOOTER,
             margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
    return out


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch() if "--chromium" in sys.argv else p.chromium.launch(channel="msedge")
        page = browser.new_page()
        for f in FILES:
            print("wrote", render(page, f))
        browser.close()


if __name__ == "__main__":
    main()
