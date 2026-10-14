"""Independent check that data/ matches the official files exactly.

For every language: the gzip file matches index.json (size + SHA-256), and every row in it is
identical, cell by cell, to the same row of the original Excel file in source/excel (or, for the
API-built language, to the raw API response). Arabic extras are compared with the raw API objects.
Usage: python -I verify.py <tools_dir> <repo_dir>
"""
import gzip, hashlib, json, os, re, sys

sys.path.insert(0, sys.argv[1])
from xlsx_read import read_xlsx

REPO = sys.argv[2]
index = json.load(open(os.path.join(REPO, "data", "v1", "index.json"), "rb"))
excel_dir = os.path.join(REPO, "source", "excel")
excel = {re.match(r"HadeethEnc\.com_([a-z]+)-v", n).group(1): n for n in os.listdir(excel_dir)}
api_ar = {o["id"]: o for o in json.load(open(os.path.join(REPO, "source", "api", "hadeeths-ar.json"), "rb"))}
api_bm = {o["id"]: o for o in json.load(open(os.path.join(REPO, "source", "api", "hadeeths-bm.json"), "rb"))}

problems = 0
cells = 0
for entry in index["languages"]:
    code = entry["code"]
    raw = open(os.path.join(REPO, entry["path"]), "rb").read()
    assert len(raw) == entry["bytes"], code
    assert hashlib.sha256(raw).hexdigest() == entry["sha256"], code
    pack = json.loads(gzip.decompress(raw))
    assert pack["lang"] == code and pack["version"] == entry["version"], code
    assert len(pack["rows"]) == entry["count"], code
    if entry["origin"] == "excel":
        rows, _ = read_xlsx(os.path.join(excel_dir, excel[code]))
        assert pack["info"] == rows[0][0], f"{code}: version block changed"
        assert pack["fields"] == rows[1], code
        original = {r[0]: r for r in rows[2:]}
        skipped = {s["id"] for s in pack.get("skipped", [])}
        assert len(original) == len(pack["rows"]) + len(skipped), code
        for row in pack["rows"]:
            if row != original[row[0]]:
                problems += 1
                print(f"{code}:{row[0]} differs from the Excel row")
            cells += len(row)
    else:
        for row in pack["rows"]:
            src = api_bm[row[0]]
            expected = {
                2: src.get("title", ""), 3: src.get("hadeeth_ar", ""), 4: src.get("hadeeth", ""),
                5: src.get("explanation_ar", ""), 6: src.get("explanation", ""),
                9: src.get("grade_ar", ""), 10: src.get("attribution_ar", ""),
                11: src.get("grade", ""), 12: src.get("attribution", ""),
            }
            for i, value in expected.items():
                if row[i] != value:
                    problems += 1
                    print(f"{code}:{row[0]} column {pack['fields'][i]} differs from the API")
            cells += len(row)
    if code == "ar":
        for hid, (reference, intro, cats) in pack["extra"].items():
            obj = api_ar[hid]
            if reference != obj.get("reference", "") or intro != obj.get("hadeeth_intro", "") or cats != (obj.get("categories") or []):
                problems += 1
                print(f"ar:{hid} extra differs from the API")
        missing = [r[0] for r in pack["rows"] if r[0] not in pack["extra"]]
        if missing:
            problems += len(missing)
            print(f"ar: {len(missing)} hadiths without API extras, e.g. {missing[:5]}")

print(f"checked {len(index['languages'])} languages, {cells} cells — problems: {problems}")
sys.exit(1 if problems else 0)
