# HadeethEnc mirror — نسخة من «موسوعة الأحاديث النبوية المترجمة»

<div dir="rtl">

هذا المستودع نسخة **غير معدّلة** من محتوى «موسوعة الأحاديث النبوية المترجمة»
([HadeethEnc.com](https://hadeethenc.com))، يستعملها تطبيق **Muflihin Pro** (قسم «موسوعة الأحاديث النبوية»)
لتنزيل المحتوى على هاتف المستخدم.

**جميع الحقوق لأصحابها: HadeethEnc.com.** المحتوى منشور هنا وفق الشروط التي وضعها المصدر لإعادة النشر
(انظر [TERMS.md](TERMS.md))، ومنها: عدم التعديل أو الإضافة أو الحذف، وذكر المصدر ورقم الإصدار،
والإبقاء على معلومات النسخة، واتباع الإصدارات الجديدة، وعدم عرض إعلانات لا تليق بالأحاديث
(والتطبيق لا يعرض أي إعلان في هذا القسم).

للملاحظات على الشرح أو الترجمة: تواصل مع فريق الموسوعة مباشرة عبر [موقعها](https://hadeethenc.com).

</div>

## Contents

| Path | What it is |
| --- | --- |
| `source/excel/HadeethEnc.com_<lang>-v<version>.xlsx` | The official Excel files, downloaded from hadeethenc.com — **byte-for-byte unchanged**. Each one starts with the source's version block ("PLEASE DON'T REMOVE THIS IMPORTANT INFORMATION!"). |
| `source/api/` | Raw responses of the official HadeethEnc API (`/api/v1`) for what the Excel files do not carry: the category tree in every language, and the Arabic per-hadith `reference` / `hadeeth_intro` / `categories`. Also the Bambara content (see *Known source issues*). Unchanged JSON objects. |
| `data/v1/hadeeths/<lang>-<version>.json.gz` | One file per language for the app: the Excel columns (`fields`) and rows (`rows`) **copied exactly**, the version block (`info`), and that language's category titles. The Arabic file also carries the API fields (`extra`) and the category tree (`parents`). |
| `data/v1/index.json` | Every language with its source version, last update, number of hadiths, file size and SHA-256. The app verifies each file against it. |
| `tools/` | The scripts that built `data/` from `source/` (Python, standard library only). |

No text is edited, translated, shortened or normalised anywhere in this repository. Conversion is
limited to the container format (Excel/JSON → compact JSON).

## Known source issues (to report to the source)

- **Bambara (`bm`)**: the official Excel file stores the whole sheet in a single cell that is cut at
  Excel's 32,767-character limit, so it is unusable. The Bambara file in `data/` is therefore built
  from the official API responses (kept in `source/api/hadeeths-bm.json`); the benefit lines are joined
  with a new line as in the Excel files.
- **Punjabi (`pa`) hadith 3791**: the row has its columns shifted in the official Excel file. It is left
  out of `data/` (listed under `skipped` in the Punjabi file) until the source fixes it; it is still in
  the original file under `source/excel/`.

## Updating

1. Download the latest Excel files from hadeethenc.com (and the API data with `tools/fetch_api.py`).
2. Run `tools/build.py` with a higher revision number — it copies the originals, rebuilds `data/`, and writes that `revision` to
   `data/v1/index.json`.
3. Commit, push, then purge jsDelivr for `data/v1/index.json`.

The app checks `index.json` and downloads any language whose version changed, so updates reach users
without an app update.
