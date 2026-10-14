"""Builds the mirror repository layout from the official HadeethEnc files.

  source/excel/*.xlsx            the official Excel files, byte-for-byte unchanged
  source/api/...                 raw API responses (fields the Excel files do not carry)
  data/v1/hadeeths/<lang>-<v>.json.gz   one file per language for the app (text unchanged)
  data/v1/index.json             versions, counts, sizes, SHA-256

No text is edited: every cell value is copied exactly as it is in the Excel file / API response.
Usage: python -I build.py <tools_dir> <hen_dir> <repo_dir> <revision>
"""
import gzip, hashlib, json, os, re, shutil, sys, datetime

sys.path.insert(0, sys.argv[1])
from xlsx_read import read_xlsx

HEN, REPO, REVISION = sys.argv[2], sys.argv[3], int(sys.argv[4])
XLSX = os.path.join(HEN, "xlsx")
API = os.path.join(HEN, "api")
DATA = os.path.join(REPO, "data", "v1")
FILE_RE = re.compile(r"HadeethEnc\.com_([a-z]+)-v([\d.]+)\.xlsx$")
INFO_RE = re.compile(r"Last update: ([^(]+)\(v([\d.]+)\)")
AR_FIELDS = ["id", "title", "hadith_text", "explanation", "word_meanings", "benefits", "grade", "takhrij", "link"]
TR_FIELDS = ["id", "title_ar", "title", "hadith_text_ar", "hadith_text", "explanation_ar", "explanation",
             "benefits_ar", "benefits", "grade_ar", "takhrij_ar", "grade", "takhrij", "lang", "link"]
BROKEN_EXCEL = {"bm"}  # whole sheet stored in one cell and cut at Excel's 32,767-character limit


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=1).encode())


def write_gz(path, obj):
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()
    gz = gzip.compress(raw, compresslevel=9, mtime=0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(gz)
    return {"bytes": len(gz), "rawBytes": len(raw), "sha256": hashlib.sha256(gz).hexdigest()}


def load_json(path):
    with open(path, "rb") as f:
        return json.load(f)


languages = {l["code"]: l["native"] for l in load_json(os.path.join(API, "languages.json"))}
files = {}
for name in sorted(os.listdir(XLSX)):
    m = FILE_RE.match(name)
    files[m.group(1)] = (name, m.group(2))

# 1) originals, unchanged
shutil.rmtree(os.path.join(REPO, "source"), ignore_errors=True)
shutil.rmtree(os.path.join(REPO, "data"), ignore_errors=True)
os.makedirs(os.path.join(REPO, "source", "excel"))
for name, _ in files.values():
    shutil.copyfile(os.path.join(XLSX, name), os.path.join(REPO, "source", "excel", name))
os.makedirs(os.path.join(REPO, "source", "api", "categories"), exist_ok=True)
shutil.copyfile(os.path.join(API, "languages.json"), os.path.join(REPO, "source", "api", "languages.json"))
for name in sorted(os.listdir(os.path.join(API, "categories"))):
    shutil.copyfile(os.path.join(API, "categories", name), os.path.join(REPO, "source", "api", "categories", name))

ar_details = {}
for name in os.listdir(os.path.join(API, "ar")):
    if name.endswith(".json"):
        obj = load_json(os.path.join(API, "ar", name))
        ar_details[obj["id"]] = obj
bm_details = {}
if os.path.isdir(os.path.join(API, "bm")):
    for name in os.listdir(os.path.join(API, "bm")):
        if name.endswith(".json"):
            obj = load_json(os.path.join(API, "bm", name))
            bm_details[obj["id"]] = obj
dump_json(os.path.join(REPO, "source", "api", "hadeeths-ar.json"), [ar_details[k] for k in sorted(ar_details, key=int)])
dump_json(os.path.join(REPO, "source", "api", "hadeeths-bm.json"), [bm_details[k] for k in sorted(bm_details, key=int)])


def categories_for(lang):
    path = os.path.join(API, "categories", f"{lang}.json")
    if not os.path.exists(path):
        return []
    return [[c["id"], c["title"], int(c["hadeeths_count"])] for c in load_json(path)]


report = []
index_langs = []
ar_ids = None
for lang in sorted(files, key=lambda c: (c != "ar", c)):
    name, version = files[lang]
    rows, _ = read_xlsx(os.path.join(XLSX, name))
    info = rows[0][0]
    upd = INFO_RE.search(info)
    updated = upd.group(1).strip() if upd else ""
    skipped = []
    if lang in BROKEN_EXCEL:
        origin = "api"
        fields = TR_FIELDS
        data = []
        for hid in sorted(bm_details, key=int):
            d = bm_details[hid]
            ar = ar_details.get(hid, {})
            data.append([
                hid, ar.get("title", ""), d.get("title", ""), d.get("hadeeth_ar", ""), d.get("hadeeth", ""),
                d.get("explanation_ar", ""), d.get("explanation", ""),
                "\n".join(h.rstrip("\r") for h in d.get("hints_ar") or []),
                "\n".join(h.rstrip("\r") for h in d.get("hints") or []),
                d.get("grade_ar", ""), d.get("attribution_ar", ""), d.get("grade", ""), d.get("attribution", ""),
                "bm", f"https://hadeethenc.com/bm/browse/hadith/{hid}",
            ])
        # the broken cell starts with the same version block as the other files: keep only that block
        block = re.match(r'^"?(#-+.*?\s#-{5,})', info, re.S)
        info = block.group(1) if block else info[:500]
    else:
        origin = "excel"
        fields = rows[1]
        expected = AR_FIELDS if lang == "ar" else TR_FIELDS
        assert fields == expected, (lang, fields)
        data = []
        for row in rows[2:]:
            if len(row) != len(fields):
                skipped.append({"id": row[0], "reason": f"row has {len(row)} columns instead of {len(fields)} in the source file"})
                continue
            data.append(row)
    ids = [r[0] for r in data]
    assert len(ids) == len(set(ids)), lang
    if lang == "ar":
        ar_ids = set(ids)
    else:
        assert set(ids) <= ar_ids, (lang, sorted(set(ids) - ar_ids)[:5])
    payload = {
        "lang": lang,
        "native": languages.get(lang, lang),
        "version": version,
        "updated": updated,
        "origin": origin,
        "info": info,
        "fields": fields,
        "rows": data,
        "categories": categories_for(lang),
    }
    if skipped:
        payload["skipped"] = skipped
    if lang == "ar":
        missing = [hid for hid in ids if hid not in ar_details]
        payload["extraFields"] = ["reference", "hadeeth_intro", "categories"]
        payload["extra"] = {
            hid: [ar_details[hid].get("reference", ""), ar_details[hid].get("hadeeth_intro", ""), ar_details[hid].get("categories") or []]
            for hid in ids if hid in ar_details
        }
        payload["parents"] = {c["id"]: c["parent_id"] for c in load_json(os.path.join(API, "categories", "ar.json"))}
        if missing:
            payload["extraMissing"] = missing
    rel = f"data/v1/hadeeths/{lang}-{version}.json.gz"
    meta = write_gz(os.path.join(REPO, rel), payload)
    index_langs.append({
        "code": lang, "native": languages.get(lang, lang), "version": version, "updated": updated,
        "origin": origin, "count": len(data), "path": rel, **meta,
    })
    report.append((lang, version, origin, len(data), len(skipped), meta["bytes"]))

index = {
    "schema": 1,
    "revision": REVISION,
    "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source": {
        "name": "HadeethEnc.com",
        "url": "https://hadeethenc.com",
        "terms": "https://hadeethenc.com/ar/home",
    },
    "languages": index_langs,
}
dump_json(os.path.join(DATA, "index.json"), index)

total = 0
for lang, version, origin, n, sk, size in report:
    total += size
    print(f"{lang:4} v{version:7} {origin:5} hadiths={n:5} skipped={sk} gz={size/1e6:.2f}MB")
print(f"languages={len(report)} total gz={total/1e6:.1f}MB")
