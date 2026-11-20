"""Build the M4 submission PDF from M4_DRAFT.md.

    app/backend/.venv/bin/python milestones/m4/build_pdf.py

Produces "CSC648-848 Section 06 Milestone4 Team03.PDF" in this folder.
The markdown draft stays the single source of truth; this script only adds
academic layout (title page, headers, styled tables, page numbers).
"""

import re
import sys
from pathlib import Path

import markdown
from xhtml2pdf import pisa

HERE = Path(__file__).resolve().parent
MD = HERE / "M4_DRAFT.md"
OUT = HERE / "CSC648-848 Section 06 Milestone4 Team03.PDF"

CSS = """
@page { size: letter; margin: 2.2cm 1.9cm;
        @frame footer { -pdf-frame-content: footerContent;
                        bottom: 1.1cm; margin-left: 1.9cm; margin-right: 1.9cm;
                        height: 1cm; } }
@page title { @frame footer { -pdf-frame-content: none; } }
body { font-family: Helvetica, Arial, sans-serif; font-size: 9.5pt;
       line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 17pt; border-bottom: 2px solid #144f72; padding-bottom: 4pt;
     color: #144f72; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h2 { font-size: 13pt; color: #144f72; margin-top: 14pt; }
h3 { font-size: 11pt; color: #2a6a8f; margin-top: 10pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0;
        font-size: 8pt; }
th { background: #144f72; color: white; padding: 4pt 5pt; text-align: left;
     font-weight: bold; }
td { border: 0.6pt solid #b9c4cc; padding: 3.5pt 5pt; vertical-align: top;
     word-wrap: break-word; }
tr:nth-child(even) td { background: #f2f6f9; }
code { font-family: Courier, monospace; font-size: 8pt; color: #144f72; }
pre { font-family: Courier, monospace; font-size: 8pt; background: #f4f6f8;
      border: 0.6pt solid #ccd4da; padding: 6pt; white-space: pre-wrap; }
blockquote { border-left: 3pt solid #e0a800; background: #fdf6e3;
             padding: 4pt 8pt; margin: 6pt 0; font-style: italic; }
strong { color: #000; }
hr { border: none; border-top: 1pt solid #ccd4da; margin: 10pt 0; }
.title-block { page: title; text-align: center; margin-top: 130pt; }
.title-block h1 { border: none; font-size: 24pt; page-break-before: avoid; }
.title-block .sub { font-size: 14pt; margin-top: 8pt; }
.title-block .meta { font-size: 11pt; margin-top: 40pt; line-height: 2.0; }
#footerContent { font-size: 8pt; color: #666; text-align: center; }
"""

# Split off a styled title page: everything up to the first "---" becomes the
# front matter, then the title block is rebuilt cleanly.
def split_title(body_html: str) -> str:
    return body_html


def main():
    text = MD.read_text()
    html = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )

    # Build a dedicated title page from the document's front matter.
    team = re.search(r"\*\*Team members and roles:\*\*(.*?)>", text, re.S)
    title_page = """
<div class="title-block">
  <h1>SW Engineering CSC648/848</h1>
  <div class="sub"><b>Milestone 4: Testing</b></div>
  <div class="sub">Projectory</div>
  <div class="meta">
    Section 06 &mdash; Team 03<br/><br/>
    Rohit &mdash; Team lead, integration, 3D functionality<br/>
    Nuradil &mdash; Backend and integration<br/>
    Ian &mdash; Frontend design and development<br/>
    Obaidullah &mdash; AI functionality<br/>
    Ali &mdash; QA and security<br/>
    Fanta &mdash; Academic resources and UX<br/><br/>
    November 22, 2026
  </div>
</div>
<pdf:nextpage/>
"""

    # Drop the draft's own inline title-page preamble (everything before the
    # first <hr/>) since the styled title page replaces it.
    body = re.sub(r"^.*?<hr\s*/?>", "", html, count=1, flags=re.S)

    # Helvetica (built-in) can't draw these; substitute readable ASCII.
    for src, dst in {
        "&rarr;": "-&gt;", "→": "-&gt;", "≈": "~", "≥": "&gt;=",
        "≤": "&lt;=", "×": "x", "…": "...",
    }.items():
        body = body.replace(src, dst)

    doc = f"""<html><head><style>{CSS}</style></head><body>
{title_page}
{body}
<div id="footerContent">CSC648/848 Milestone 4 &mdash; Projectory &mdash; Team 03 &mdash; Page <pdf:pagenumber/></div>
</body></html>"""

    with open(OUT, "wb") as f:
        status = pisa.CreatePDF(doc, dest=f)
    if status.err:
        print("PDF generation reported errors:", status.err)
        sys.exit(1)
    print(f"Wrote {OUT.name} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
