# وضعیت فعلی منبع و محیط اجرا

تاریخ بررسی: ۱۷ اوت ۲۰۲۶  
هدف: مشخص کردن اینکه آیا محیط زنده برای ارزیابی دانش‌بنیان فردا قابل اتکا است یا نه.

## نتیجه کوتاه

محیط زنده برای نمایش محصول **مناسب است**، با یک هشدار منبع:

- شاخه محصول روی سرور و مخزن محلی یکی است: `restart/sprint5f-fix2-runtime-ui-closure`
- کد محصول پذیرفته‌شده Sprint 5F-Fix-2 روی سرور در حال اجرا است.
- `HEAD` گیت سرور چند commit مستندات/دمو عقب‌تر از مخزن محلی است. این اختلاف قابلیت محصول را عوض نمی‌کند، اما باید در جلسه گفته شود.

ادعای قابلیت‌ها در بقیه اسناد این بسته بر اساس همین شاخه و کد فعلی است، نه نقشه راه.

## منبع محلی (workspace)

| مورد | مقدار |
| --- | --- |
| شاخه | `restart/sprint5f-fix2-runtime-ui-closure` |
| Commit | `65493bfb58bece157eb6b7dd8220f0259380b57b` |
| توضیح آخرین commit | `chore: add IT procurement demo dataset for 1405` |
| وضعیت کاری | فقط اسناد ارزیابی در حال تولید است |

۳۰ commit اخیر روی همین شاخه شامل بستن Sprint 5F-Fix-2، تخصیص تأمین، RBAC و دیتای دمو ۱۴۰۵ است.

## منبع مستقر روی سرور

| مورد | مقدار |
| --- | --- |
| مسیر استقرار | `/root/pdss` |
| شاخه | `restart/sprint5f-fix2-runtime-ui-closure` |
| Commit گیت سرور | `ad55a733b6648638a150b7cf6fc9fc1d0251c31a` |
| توضیح | `chore: close procurement assignment table runtime deployment` |
| فاصله با workspace | سرور `65493bf` را ندارد (اسکریپت دمو + گزارش دمو + اسناد reconciliation) |

اسکریپت دمو قبلاً روی فایل‌سیستم سرور کپی و اجرا شده است. دیتای `DEMO_IT_1405_` روی دیتابیس زنده موجود است.

## سرویس‌های Docker

دستور: `cd /root/pdss && docker compose ps`

| سرویس | وضعیت | پورت |
| --- | --- | --- |
| `pdss-backend-1` | Up, healthy | `8000` |
| `pdss-frontend-1` | Up | `3000` |
| `pdss-postgres-1` | Up, healthy | `5432` |

`docker compose down -v` اجرا نشده است.

## سلامت Backend

```text
GET http://127.0.0.1:8000/health
{"status":"healthy","version":"1.0.0-rc1","product":"Rivar","producer":"Corbit"}
```

```text
GET http://127.0.0.1:8000/openapi.json
HTTP 200
title: Rivar API
version: 1.0.0-rc1
paths: 179
```

## آدرس‌های نمایش زنده

| مورد | آدرس |
| --- | --- |
| Frontend | `http://193.162.129.58:3000` |
| Backend API | `http://193.162.129.58:8000` |
| Health | `http://193.162.129.58:8000/health` |
| OpenAPI | `http://193.162.129.58:8000/openapi.json` |

ورود از صفحه اصلی `/` انجام شود. لینک مستقیم `/dashboard` یا `/procurement` ممکن است در لایه استاتیک 404 بدهد.

## هویت محصول در runtime

از `backend/app/app_metadata.py` و `backend/VERSION`:

- نام محصول: `Rivar`
- تولیدکننده: `Corbit`
- نسخه: `1.0.0-rc1`
- وضعیت انتشار: pilot / RC

برند در Login، Layout، title، manifest و `/health` دیده می‌شود. نام‌های قدیمی `PDSS` / `procurement_dss` هنوز در Docker و بعضی بسته‌های نصب باقی است.

## آیا سرور برای ارزیابی زنده مناسب است؟

**بله، با این شرایط:**

1. سه کانتینر سالم هستند.
2. هویت Rivar/Corbit از `/health` قابل نمایش است.
3. دیتای دمو IT ۱۴۰۵ روی همین دیتابیس موجود است (۳۰ پروژه، ۹۰۰ قلم، ۲۷۰ نهایی‌شده).
4. کد محصول همان شاخه پذیرفته‌شده 5F-Fix-2 است.

## هشدارها

1. `HEAD` گیت سرور = `ad55a73`؛ workspace/origin = `65493bf`. اختلاف عمدتاً اسکریپت دمو و اسناد است، نه قابلیت جدید محصول.
2. Frontend با `npm start` داخل Docker اجرا می‌شود، نه لزوماً build استاتیک nginx.
3. بعضی feature flagهای پوشش بسته پیش‌فرض خاموش‌اند؛ lock ناقص را بدون روشن بودن flag نمی‌توان به‌عنوان رفتار اجباری زنده نشان داد.
4. تست کامل backend به‌خاطر import از پیش موجود `financial_projections` در collection شکست می‌خورد. این نقص تست است، نه اثبات نبود کل محصول.
5. رمزها و مقادیر `.env` در جلسه نشان داده نشوند. فقط کاربران دمو استفاده شوند.

## تأیید مجدد قبل از تحویل بسته

تاریخ: ۱۷ اوت ۲۰۲۶، پس از تولید اسناد.

| بررسی | نتیجه |
| --- | --- |
| `docker compose ps` | backend healthy، frontend Up، postgres healthy |
| `GET /health` | `healthy` / `Rivar` / `Corbit` / `1.0.0-rc1` |
| OpenAPI | HTTP 200 |
| `--mode verify` دمو ۱۴۰۵ | ۳۰ پروژه، ۹۰۰ قلم، ۲۷۰ نهایی، ۱۲ تأمین‌کننده، ۶۴۸ گزینه/بسته |
| `pytest tests -q` | collection error در `test_phase13f_financial_projection_engine.py` |
| `npm run build` | موفق؛ `main.03b9b674.js` با هشدار ESLint موجود |
