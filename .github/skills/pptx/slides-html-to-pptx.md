# Slides HTML to Native PPTX

Use this workflow when converting an LLM Wiki `*.slides.html` artifact into PowerPoint.

## Goal

Create an editable `.pptx` that preserves the `slides.html` content structure. The output should use native PowerPoint text boxes, tables, and shapes. Do not screenshot each slide unless the user explicitly asks for an image-only deck.

## Default Path

1. Read the source Markdown artifact if available.
2. Read or inspect `*.slides.html`.
3. Build a slide inventory:
   - slide count from `<section class="slide">`;
   - slide titles;
   - bullet counts;
   - table count and column names;
   - key strings such as URLs, company names, dates, metrics, and Provenance paths.
4. Generate `*.slides-native.pptx`.
5. Extract PPTX text and validate coverage against the inventory.
6. Open-test the PPTX with PowerPoint or LibreOffice when available.

## Preferred Generators

Use this priority order:

1. PowerPoint COM on Windows.
2. `python-pptx` or PptxGenJS using a known-good base template.
3. OOXML modification of an existing PowerPoint-saved template.
4. Hand-written OOXML only as a last resort.

## Base Template

When available, use:

`templates/wiki-teal-16x9-base.pptx`

This template is intended to provide a PowerPoint-saved package structure, 16:9 slide size, and Wiki Teal visual defaults. It is a baseline, not a content source. Replace or create slide contents as native objects.

## Content Preservation Rules

- Keep every slide-level message from `slides.html`.
- Preserve detail tables by splitting across slides before dropping columns.
- Preserve table column names. If a table is explicitly summarized, label it as `Summary`, `主要列のみ`, or equivalent.
- Preserve URLs, company names, source paths, and Provenance.
- Do not invent new claims in PPTX. Update the Markdown source first if content changes are needed.

## PowerPoint COM Notes

On Windows, COM-generated decks are often the most compatible with desktop PowerPoint.

Basic smoke test:

```powershell
$p=(Resolve-Path "output.pptx").Path
$ppt=New-Object -ComObject PowerPoint.Application
$ppt.Visible=-1
$pres=$ppt.Presentations.Open($p, -1, 0, 0)
$count=$pres.Slides.Count
$pres.Close(); $ppt.Quit()
"opened slides=$count"
```

If this hangs, check for an existing PowerPoint modal dialog or lock file (`~$...pptx`) and ask the user to close PowerPoint before retrying.

## Coverage Check Example

Inspect the generated package:

```python
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

p = Path("output.pptx")
z = ZipFile(p)
slides = sorted(n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
texts = []
for n in slides:
    root = ET.fromstring(z.read(n))
    texts += [el.text or "" for el in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t")]

joined = "".join(texts)
checks = [
    "運営企業URL",
    "情報",
    "raw/inbox/source.md",
]
print("slides", len(slides))
print("text_runs", len(texts))
print("tables", sum(z.read(n).count(b"<a:tbl>") for n in slides))
print("media_files", len([n for n in z.namelist() if n.startswith("ppt/media/")]))
for c in checks:
    print(("OK" if c in joined else "MISS"), c)
```

PowerPoint may split mixed Japanese/ASCII strings across multiple text runs. For coverage checks, join text runs before searching.
