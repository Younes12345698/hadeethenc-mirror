"""Fetches the fields the official Excel files do not carry (categories tree, per-hadith category ids,
references) plus the Bambara content (its Excel file is broken at the source).

Polite: one request at a time with a pause, resumable (already saved responses are skipped).
Raw API responses are saved unchanged under <out>/api/.
Usage: python -I fetch_api.py <tools_dir> <hen_dir>
"""
import json, os, sys, time, urllib.request, urllib.error

sys.path.insert(0, sys.argv[1])
from xlsx_read import read_xlsx

HEN = sys.argv[2]
API = "https://hadeethenc.com/api/v1"
OUT = os.path.join(HEN, "api")
PAUSE = 0.35


def get(url, tries=4):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MuflihinPro-mirror/1.0 (+https://muflihinpro.com)"})
            with urllib.request.urlopen(req, timeout=40) as resp:
                body = resp.read()
            json.loads(body)  # must be valid JSON
            return body
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            wait = 3 * (attempt + 1)
            print(f"  retry {attempt + 1} after error {exc!r} for {url}", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"failed: {url}")


def save(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(body)
    os.replace(tmp, path)


def fetch(url, path):
    if os.path.exists(path):
        return json.load(open(path, "rb"))
    body = get(url)
    save(path, body)
    time.sleep(PAUSE)
    return json.loads(body)


langs = json.loads(get(f"{API}/languages"))
save(os.path.join(OUT, "languages.json"), json.dumps(langs, ensure_ascii=False).encode())
codes = [l["code"] for l in langs]
print("languages:", len(codes), flush=True)

for code in codes:
    fetch(f"{API}/categories/list/?language={code}", os.path.join(OUT, "categories", f"{code}.json"))
print("categories done", flush=True)

xlsx_dir = os.path.join(HEN, "xlsx")
ar_file = next(n for n in os.listdir(xlsx_dir) if n.startswith("HadeethEnc.com_ar-"))
rows, _ = read_xlsx(os.path.join(xlsx_dir, ar_file))
ids = [r[0] for r in rows[2:]]
print("arabic ids:", len(ids), flush=True)

bm_ids = []
for i, hid in enumerate(ids):
    one = fetch(f"{API}/hadeeths/one/?language=ar&id={hid}", os.path.join(OUT, "ar", f"{hid}.json"))
    if "bm" in (one.get("translations") or []):
        bm_ids.append(hid)
    if i % 200 == 0:
        print(f"ar {i}/{len(ids)}", flush=True)
print("arabic details done; bambara ids:", len(bm_ids), flush=True)

for hid in bm_ids:
    fetch(f"{API}/hadeeths/one/?language=bm&id={hid}", os.path.join(OUT, "bm", f"{hid}.json"))
print("ALL DONE", flush=True)
