from __future__ import annotations

import argparse
import html
import re
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from bs4 import BeautifulSoup


EMU_PER_INCH = 914400
SLIDE_W = 13.333333
SLIDE_H = 7.5
CX = int(SLIDE_W * EMU_PER_INCH)
CY = int(SLIDE_H * EMU_PER_INCH)


def emu(inches: float) -> int:
    return int(inches * EMU_PER_INCH)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def local_name(tag_name: str) -> str:
    return tag_name.split("}")[-1] if "}" in tag_name else tag_name


def get_text(el) -> str:
    return clean_text(el.get_text(" ", strip=True)) if el else ""


def collect_slide_data(section) -> dict:
    title = get_text(section.find(["h1", "h2"]))
    eyebrow = get_text(section.find(class_="eyebrow") or section.find(class_="section-label"))
    lead = get_text(section.find(class_="lead"))
    meta = get_text(section.find(class_="meta"))
    bullets = [get_text(li) for li in section.find_all("li")]

    cards = []
    for card in section.find_all(class_="card"):
        cards.append(
            {
                "badge": get_text(card.find(class_="badge")),
                "title": get_text(card.find("h3")),
                "body": get_text(card.find("p")),
            }
        )

    tables = []
    for table in section.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [get_text(c) for c in tr.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)

    paragraphs = []
    for p in section.find_all("p"):
        classes = set(p.get("class", []))
        if classes & {"eyebrow", "section-label", "lead", "meta"}:
            continue
        text = get_text(p)
        if text:
            paragraphs.append(text)

    return {
        "title": title,
        "eyebrow": eyebrow,
        "lead": lead,
        "meta": meta,
        "bullets": bullets,
        "cards": cards,
        "tables": tables,
        "paragraphs": paragraphs,
    }


def a_text(text: str, size: int = 1800, bold: bool = False, color: str = "172033") -> str:
    attrs = f' lang="ja-JP" sz="{size}"'
    if bold:
        attrs += ' b="1"'
    return (
        f"<a:r><a:rPr{attrs}><a:solidFill><a:srgbClr val=\"{color}\"/></a:solidFill>"
        f"</a:rPr><a:t>{escape(text)}</a:t></a:r>"
    )


def text_box(shape_id: int, x: float, y: float, w: float, h: float, paragraphs: list[list[dict]]) -> str:
    p_xml = []
    for para in paragraphs:
        runs = "".join(
            a_text(
                run.get("text", ""),
                size=run.get("size", 1800),
                bold=run.get("bold", False),
                color=run.get("color", "172033"),
            )
            for run in para
            if run.get("text")
        )
        p_xml.append(f"<a:p>{runs}<a:endParaRPr lang=\"ja-JP\"/></a:p>")
    body = "".join(p_xml) or "<a:p/>"
    return f"""
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="{shape_id}" name="TextBox {shape_id}"/>
          <p:cNvSpPr txBox="1"/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:noFill/>
        </p:spPr>
        <p:txBody>
          <a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0"/>
          <a:lstStyle/>
          {body}
        </p:txBody>
      </p:sp>
    """


def rect(shape_id: int, x: float, y: float, w: float, h: float, fill: str, line: str = "D9E1EA") -> str:
    return f"""
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="{shape_id}" name="Rect {shape_id}"/>
          <p:cNvSpPr/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>
          <a:ln><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>
        </p:spPr>
      </p:sp>
    """


def bullet_box(shape_id: int, bullets: list[str], x: float, y: float, w: float, h: float, size: int = 1900) -> str:
    paras = [[{"text": f"• {b}", "size": size}] for b in bullets]
    return text_box(shape_id, x, y, w, h, paras)


def table_shape(shape_id_start: int, rows: list[list[str]], x: float, y: float, w: float, h: float) -> tuple[str, int]:
    max_cols = max(len(r) for r in rows)
    row_h = h / max(len(rows), 1)
    col_w = w / max_cols
    xml = []
    sid = shape_id_start
    for r_idx, row in enumerate(rows):
        for c_idx in range(max_cols):
            text = row[c_idx] if c_idx < len(row) else ""
            fill = "E7F2F2" if r_idx == 0 else "FFFFFF"
            color = "18383B" if r_idx == 0 else "172033"
            bold = r_idx == 0
            cell_x = x + c_idx * col_w
            cell_y = y + r_idx * row_h
            xml.append(rect(sid, cell_x, cell_y, col_w, row_h, fill))
            sid += 1
            size = 900 if len(rows) > 8 else 1050
            xml.append(
                text_box(
                    sid,
                    cell_x + 0.04,
                    cell_y + 0.04,
                    max(col_w - 0.08, 0.1),
                    max(row_h - 0.06, 0.1),
                    [[{"text": text, "size": size, "bold": bold, "color": color}]],
                )
            )
            sid += 1
    return "\n".join(xml), sid


def card_shapes(shape_id_start: int, cards: list[dict], x: float, y: float, w: float, h: float) -> tuple[str, int]:
    xml = []
    sid = shape_id_start
    cols = 3
    rows = 2
    gap = 0.18
    cw = (w - gap * (cols - 1)) / cols
    ch = (h - gap * (rows - 1)) / rows
    for idx, card in enumerate(cards[:6]):
        cx_pos = x + (idx % cols) * (cw + gap)
        cy_pos = y + (idx // cols) * (ch + gap)
        xml.append(rect(sid, cx_pos, cy_pos, cw, ch, "FCFEFE"))
        sid += 1
        lines = [
            [{"text": card.get("badge", ""), "size": 1050, "bold": True, "color": "0F766E"}],
            [{"text": card.get("title", ""), "size": 1500, "bold": True, "color": "172033"}],
            [{"text": card.get("body", ""), "size": 1050, "color": "405255"}],
        ]
        xml.append(text_box(sid, cx_pos + 0.16, cy_pos + 0.14, cw - 0.28, ch - 0.24, lines))
        sid += 1
    return "\n".join(xml), sid


def slide_xml(data: dict, slide_no: int) -> str:
    sid = 2
    shapes = [rect(1, 0, 0, SLIDE_W, 0.1, "0F766E", "0F766E")]

    if slide_no == 1:
        shapes.append(text_box(sid, 0.9, 1.18, 10.9, 0.35, [[{"text": data["eyebrow"], "size": 1500, "bold": True, "color": "0F766E"}]]))
        sid += 1
        shapes.append(text_box(sid, 0.9, 1.75, 10.4, 1.35, [[{"text": data["title"], "size": 3600, "bold": True}]]))
        sid += 1
        shapes.append(text_box(sid, 0.9, 3.25, 10.4, 1.15, [[{"text": data["lead"], "size": 1800, "color": "344548"}]]))
        sid += 1
        shapes.append(text_box(sid, 0.9, 5.25, 10.8, 0.3, [[{"text": data["meta"], "size": 1200, "color": "5F6B7A"}]]))
        sid += 1
    else:
        shapes.append(text_box(sid, 0.72, 0.55, 7.8, 0.3, [[{"text": data["eyebrow"], "size": 1150, "bold": True, "color": "0F766E"}]]))
        sid += 1
        shapes.append(text_box(sid, 0.72, 0.9, 11.2, 0.65, [[{"text": data["title"], "size": 2500, "bold": True}]]))
        sid += 1
        if data["cards"]:
            card_xml, sid = card_shapes(sid, data["cards"], 0.72, 1.72, 11.85, 4.55)
            shapes.append(card_xml)
        elif data["tables"]:
            table_xml, sid = table_shape(sid, data["tables"][0], 0.62, 1.78, 12.1, 4.72)
            shapes.append(table_xml)
        elif data["bullets"]:
            shapes.append(bullet_box(sid, data["bullets"], 0.85, 1.72, 11.45, 4.65, 1650 if len(data["bullets"]) > 4 else 1850))
            sid += 1
        else:
            text = "\n".join(data["paragraphs"])
            shapes.append(text_box(sid, 0.85, 1.85, 11.0, 4.0, [[{"text": text, "size": 1500}]]))
            sid += 1

    shapes.append(text_box(900, 12.0, 7.08, 0.6, 0.25, [[{"text": str(slide_no), "size": 1050, "color": "8190A0"}]]))

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      {''.join(shapes)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"""


def find_template(output: Path, explicit_template: Path | None = None) -> Path | None:
    if explicit_template:
        return explicit_template if explicit_template.exists() else None
    if output.parent.exists():
        for candidate in output.parent.glob("*.slides-native.pptx"):
            if candidate.resolve() != output.resolve():
                return candidate
    for candidate in Path("artifacts").glob("**/*.slides-native.pptx"):
        if candidate.resolve() != output.resolve():
            return candidate
    return None


def write_pptx(slides: list[dict], output: Path, template: Path | None = None) -> None:
    template = find_template(output, template)
    if template and template.exists():
        write_pptx_from_template(slides, output, template)
        return

    slide_overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, len(slides) + 1)
    )
    slide_ids = "\n".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i}"/>' for i in range(1, len(slides) + 1)
    )
    pres_rels = "\n".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, len(slides) + 1)
    )
    master_rid = len(slides) + 1
    pres_rels += f'\n<Relationship Id="rId{master_rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slide_overrides}
</Types>""",
        )
        z.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>""",
        )
        z.writestr(
            "docProps/core.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>HTML Slides Artifact</dc:title>
  <dc:creator>LLM Wiki</dc:creator>
  <cp:lastModifiedBy>LLM Wiki</cp:lastModifiedBy>
</cp:coreProperties>""",
        )
        z.writestr(
            "docProps/app.xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>LLM Wiki</Application><Slides>{len(slides)}</Slides>
</Properties>""",
        )
        z.writestr(
            "ppt/presentation.xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{master_rid}"/></p:sldMasterIdLst>
  <p:sldIdLst>{slide_ids}</p:sldIdLst>
  <p:sldSz cx="{CX}" cy="{CY}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>""",
        )
        z.writestr(
            "ppt/_rels/presentation.xml.rels",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{pres_rels}
</Relationships>""",
        )
        z.writestr(
            "ppt/slideMasters/slideMaster1.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
</p:sldMaster>""",
        )
        z.writestr(
            "ppt/slideMasters/_rels/slideMaster1.xml.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>""",
        )
        z.writestr(
            "ppt/slideLayouts/slideLayout1.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>""",
        )
        z.writestr(
            "ppt/slideLayouts/_rels/slideLayout1.xml.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>""",
        )
        z.writestr(
            "ppt/theme/theme1.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="LLM Wiki">
  <a:themeElements>
    <a:clrScheme name="Wiki Teal"><a:dk1><a:srgbClr val="172033"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="5F6B7A"/></a:dk2><a:lt2><a:srgbClr val="F3F5F7"/></a:lt2><a:accent1><a:srgbClr val="0F766E"/></a:accent1><a:accent2><a:srgbClr val="D9E1EA"/></a:accent2><a:accent3><a:srgbClr val="EDF7F5"/></a:accent3><a:accent4><a:srgbClr val="8A5A00"/></a:accent4><a:accent5><a:srgbClr val="FFF4D8"/></a:accent5><a:accent6><a:srgbClr val="405255"/></a:accent6><a:hlink><a:srgbClr val="0D6770"/></a:hlink><a:folHlink><a:srgbClr val="0D6770"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="Office"><a:majorFont><a:latin typeface="Yu Gothic"/><a:ea typeface="Yu Gothic"/></a:majorFont><a:minorFont><a:latin typeface="Yu Gothic"/><a:ea typeface="Yu Gothic"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>""",
        )
        for idx, slide in enumerate(slides, start=1):
            z.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(slide, idx))
            z.writestr(
                f"ppt/slides/_rels/slide{idx}.xml.rels",
                """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>""",
            )


def replace_slide_overrides(content_types: str, slide_count: int) -> str:
    content_types = re.sub(
        r'<Override PartName="/ppt/slides/slide\d+\.xml" ContentType="application/vnd\.openxmlformats-officedocument\.presentationml\.slide\+xml"/>\s*',
        "",
        content_types,
    )
    overrides = "".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, slide_count + 1)
    )
    return content_types.replace("</Types>", f"{overrides}</Types>")


def presentation_xml_from_template(template_xml: str, slide_count: int) -> str:
    slide_ids = "".join(
        f'<p:sldId id="{255 + i}" r:id="rId{i + 1}"/>' for i in range(1, slide_count + 1)
    )
    if "<p:sldIdLst>" in template_xml:
        template_xml = re.sub(r"<p:sldIdLst>.*?</p:sldIdLst>", f"<p:sldIdLst>{slide_ids}</p:sldIdLst>", template_xml)
    else:
        template_xml = template_xml.replace("</p:sldMasterIdLst>", f"</p:sldMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst>")
    template_xml = re.sub(r'<p:sldMasterId id="[^"]+" r:id="[^"]+"', '<p:sldMasterId id="2147483648" r:id="rId1"', template_xml)
    return template_xml


def presentation_rels(slide_count: int) -> str:
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    ]
    rels.extend(
        f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, slide_count + 1)
    )
    base = slide_count + 2
    rels.extend(
        [
            f'<Relationship Id="rId{base}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>',
            f'<Relationship Id="rId{base + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>',
            f'<Relationship Id="rId{base + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>',
            f'<Relationship Id="rId{base + 3}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="tableStyles.xml"/>',
        ]
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(rels)
        + "</Relationships>"
    )


def write_pptx_from_template(slides: list[dict], output: Path, template: Path) -> None:
    slide_names = re.compile(r"ppt/slides/(?:_rels/)?slide\d+\.xml(?:\.rels)?$")
    with zipfile.ZipFile(template, "r") as src, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            name = item.filename
            if slide_names.match(name):
                continue
            if name == "[Content_Types].xml":
                dst.writestr(name, replace_slide_overrides(src.read(name).decode("utf-8"), len(slides)))
            elif name == "ppt/presentation.xml":
                dst.writestr(name, presentation_xml_from_template(src.read(name).decode("utf-8"), len(slides)))
            elif name == "ppt/_rels/presentation.xml.rels":
                dst.writestr(name, presentation_rels(len(slides)))
            elif name == "docProps/core.xml":
                dst.writestr(
                    name,
                    """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>HTML Slides Artifact</dc:title>
  <dc:creator>LLM Wiki</dc:creator>
  <cp:lastModifiedBy>LLM Wiki</cp:lastModifiedBy>
</cp:coreProperties>""",
                )
            elif name == "docProps/app.xml":
                dst.writestr(
                    name,
                    f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>LLM Wiki</Application><Slides>{len(slides)}</Slides>
</Properties>""",
                )
            else:
                dst.writestr(item, src.read(name))

        for idx, slide in enumerate(slides, start=1):
            dst.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(slide, idx))
            dst.writestr(
                f"ppt/slides/_rels/slide{idx}.xml.rels",
                """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>""",
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_html", type=Path)
    parser.add_argument("output_pptx", type=Path)
    parser.add_argument("--template", type=Path, default=None, help="Optional existing PPTX to use as the Open XML template.")
    args = parser.parse_args()

    soup = BeautifulSoup(args.input_html.read_text(encoding="utf-8"), "html.parser")
    sections = soup.select("section.slide")
    slides = [collect_slide_data(section) for section in sections]
    args.output_pptx.parent.mkdir(parents=True, exist_ok=True)
    write_pptx(slides, args.output_pptx, args.template)
    print(f"Wrote {args.output_pptx} ({len(slides)} slides)")


if __name__ == "__main__":
    main()
