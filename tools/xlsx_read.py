"""Minimal stdlib .xlsx reader (shared strings + inline strings), no third-party packages.

Returns the first worksheet as a list of rows (list of str), preserving cell text exactly
as stored in the workbook (no trimming, no normalisation).
"""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _text_of(si):
    # <si><t>..</t></si> or rich text <si><r><t>..</t></r>...</si>; ignore phonetic runs (<rPh>)
    parts = []
    for child in si:
        tag = child.tag.split("}")[1]
        if tag == "t":
            parts.append(child.text or "")
        elif tag == "r":
            for t in child.findall("m:t", NS):
                parts.append(t.text or "")
    return "".join(parts)


def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = [_text_of(si) for si in root.findall("m:si", NS)]
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = wb.find("m:sheets", NS)
        first = sheets[0]
        rid = first.get("{%s}id" % REL_NS)
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels:
            if rel.get("Id") == rid:
                target = rel.get("Target")
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        sheet = ET.fromstring(z.read(target))
        rows = []
        for row in sheet.find("m:sheetData", NS).findall("m:row", NS):
            cells = {}
            for c in row.findall("m:c", NS):
                ref = c.get("r")
                t = c.get("t")
                v = c.find("m:v", NS)
                if t == "s":
                    val = shared[int(v.text)] if v is not None else ""
                elif t == "inlineStr":
                    is_ = c.find("m:is", NS)
                    val = _text_of(is_) if is_ is not None else ""
                else:
                    val = v.text if v is not None and v.text is not None else ""
                cells[_col_index(ref)] = val
            if cells:
                width = max(cells) + 1
                rows.append([cells.get(i, "") for i in range(width)])
            else:
                rows.append([])
        return rows, first.get("name")
