# شروط المصدر — Source terms (HadeethEnc.com)

<div dir="rtl">

نص الشروط كما ورد في موقع الموسوعة ([hadeethenc.com](https://hadeethenc.com/ar/home)، نافذة «الشروط والسياسات»)
عند تنزيل الملفات في 14 أكتوبر 2026:

> يتاح تنزيل محتوى الترجمات وإعادة نشره، بالشروط والضوابط التالية:
>
> 1. عدم التعديل أو الإضافة أو الحذف على المحتوى.
> 2. الإشارة بوضوح للناشر وللمصدر (HadeethEnc.com).
> 3. ذكر رقم الإصدار عند إعادة نشر الترجمة.
> 4. إبقاء معلومات نسخة الترجمة الموجودة داخل المستند.
> 5. إفادة المصدر (HadeethEnc.com) بأي ملاحظة على الترجمة.
> 6. تطوير الترجمات وفق النسخ الجديدة الصادرة من المصدر (HadeethEnc.com).
> 7. عدم تضمين إعلانات لا تليق بمحتوى الأحاديث النبوية وترجماتها عند العرض.

ويذكر الموقع أن «تنزيل الملفات يتضمن الموافقة على هذه الشروط والسياسات».

</div>

## How this mirror and the Muflihin Pro app follow them

1. **No changes** — the original files are kept byte-for-byte in `source/`; `data/` copies the same cell
   values exactly (only the container format changes). The app displays the stored text as is.
2. **Credit** — this repository, every hadith screen and every shared hadith name HadeethEnc.com.
3. **Version number** — `data/v1/index.json` and every data file keep the source version; the app shows it.
4. **Version information kept** — the source's version block is kept in every data file (`info`) and shown
   in the app's "About the source" page.
5. **Notes go to the source** — the app links to the source website for notes.
6. **New versions** — `tools/` rebuilds the data from new source files; the app updates automatically.
7. **No unsuitable ads** — the app shows **no ads at all** in this section.

*This repository does not claim any rights over the content. All rights belong to HadeethEnc.com.*
