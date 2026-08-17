# چک‌لیست یک‌صفحه‌ای جلسه ارزیابی

محصول را نشان دهید، نه تیم را. چیزی را که روی صفحه نیست ادعا نکنید.

## قبل از جلسه باز کنید

- مرورگر روی `http://193.162.129.58:3000` از مسیر `/`
- تب دوم: `http://193.162.129.58:8000/health`
- ترمینال SSH روی `/root/pdss`
- ویرایشگر روی این فایل‌ها:
  - `backend/app/main.py`
  - `backend/app/models.py`
  - `backend/app/services/package_service.py`
  - `backend/app/optimization_engine_enhanced.py`
  - `docker-compose.yml`
  - `docs/evaluation/04_capability_evidence_matrix_fa.md`

Hard refresh: `Ctrl+F5`. از deep-link `/dashboard` شروع نکنید.

## آدرس‌ها

| مورد | آدرس |
| --- | --- |
| Frontend | `http://193.162.129.58:3000` |
| Health | `http://193.162.129.58:8000/health` |
| OpenAPI | `http://193.162.129.58:8000/openapi.json` |

انتظار health: `{"status":"healthy","version":"1.0.0-rc1","product":"Rivar","producer":"Corbit"}`

## کاربران دمو

| کاربر | رمز | برای چه |
| --- | --- | --- |
| `admin` | `admin123` | ورود، ممیزی، بهینه‌سازی |
| `pmo1` | `pmo123` | پروژه / نهایی‌سازی |
| `pm1` | `pm123` | اقلام / پذیرش تحویل |
| `proc1` | `proc123` | تأمین و تخصیص |
| `finance1` | `finance123` | داشبورد و مالی |

`.env` و رمز واقعی سرور را نشان ندهید.

## فرمان‌های ترمینال آماده

```bash
cd /root/pdss
docker compose ps
curl -sS http://127.0.0.1:8000/health
docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode verify
```

پشتیبان: اگر کسی خواست دیتابیس را دست بزنید، اول backup اسکریپت استقرار را نشان دهید. `docker compose down -v` ممنوع.

## توالی توضیح (۱۵ تا ۲۰ دقیقه اول)

1. Health و هویت Rivar / Corbit / RC1
2. `docker compose ps`
3. ورود `admin`
4. داشبورد از منو
5. پروژه‌های `DEMO_IT_1405_`
6. Items Master و زیرقلم
7. اقلام نهایی و تخصیص `proc1`/`proc2`
8. تأمین‌کننده متمایز، گزینه، coverage
9. بگویید lock پوشش flag-gated است
10. Optimization Enhanced و OR-Tools
11. Reports / Audit
12. کد `main.py` و بسته `release_packages/corbit-rivar-rc1`
13. محدودیت‌ها را خودتان بگویید

جزئیات دقیق‌تر: `docs/evaluation/05_live_demo_runbook_fa.md`

## اگر UI قطع شد

1. بگویید «شاهد از API و کد است»
2. `curl /health` و `docker compose ps`
3. همان قابلیت را از OpenAPI صدا بزنید
4. فایل سرویس/مدل را باز کنید
5. `--mode verify` را نشان دهید
6. به اسلاید یا ویدئو برنگردید

## چه چیزی را ادعا نکنید

- محصول نهایی تجاری کامل
- ERP یا نرم‌افزار حسابداری کامل
- اجبار سراسری RBAC در همین runtime
- رد شدن خودکار lock پوشش ناقص بدون روشن بودن هر دو flag
- استفاده از PuLP به‌عنوان حل‌کننده فعلی
- وجود router سوارشده `financial_projections`
- قفل بودن همه تصمیم‌های دمو ۱۴۰۵
- برند کامل در نام دیتابیس و بعضی بسته‌های قدیمی PDSS
- سبز بودن کل pytest در وضعیت فعلی (خطای collection فاز ۱۳F)

## جمله پایانی پیشنهادی

«Rivar محصول Corbit در وضعیت `1.0.0-rc1` است: سامانه تصمیم‌یار تأمین پروژه‌ای و نقدینگی. آنچه نشان دادیم روی سرور زنده، با داده دمو IT ۱۴۰۵، از کد همین شاخه قابل مشاهده است. محدودیت‌ها را هم نشان دادیم: pilot/RC است، بعضی کنترل‌ها flag دارند، و مسیر پس از lock را در دمو انبوه از پیش نبسته‌ایم.»
