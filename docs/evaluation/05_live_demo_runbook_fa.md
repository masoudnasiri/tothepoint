# راهنمای نمایش زنده جلسه ارزیابی

زمان پیشنهادی: ۴۵ تا ۶۰ دقیقه.  
محصول را نشان دهید، نه تیم توسعه را.

## قبل از جلسه

- [ ] سرور در دسترس است: `http://193.162.129.58:3000`
- [ ] Health: `http://193.162.129.58:8000/health` باید `Rivar` / `Corbit` / `1.0.0-rc1` بدهد
- [ ] `cd /root/pdss && docker compose ps` سه سرویس Up
- [ ] مرورگر را hard refresh کنید (`Ctrl+F5`) و از `/` وارد شوید
- [ ] کاربران دمو آماده باشند
- [ ] دیتای `DEMO_IT_1405_` را verify کنید؛ اگر موجود است cleanup نکنید
- [ ] یک ترمینال روی `/root/pdss` باز بماند
- [ ] در ویرایشگر این فایل‌ها باز باشند: `main.py`, `models.py`, `package_service.py`, `optimization_engine_enhanced.py`, `docker-compose.yml`, `create_it_procurement_demo_1405.py`

### کاربران دمو (فقط محیط آزمایش)

| کاربر | رمز | نقش پیشنهادی در دمو |
| --- | --- | --- |
| `admin` | `admin123` | ورود، کاربران، ممیزی، بهینه‌سازی |
| `pmo1` | `pmo123` | پروژه و نهایی‌سازی |
| `pm1` | `pm123` | اقلام پروژه / پذیرش تحویل |
| `proc1` | `proc123` | تأمین و تخصیص |
| `finance1` | `finance123` | داشبورد و مالی |

اگر دمو خالی شد:

```bash
cd /root/pdss
docker compose exec -T -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode verify
# فقط در صورت خالی بودن:
docker compose exec -T -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode create --skip-pre-clean
```

پشتیبان یادآوری: قبل از هر تغییر خطرناک backup بگیرید. در جلسه چیزی را reset نکنید.

## توالی نمایش

### ۱. سیستم زنده است — ۲ دقیقه

- بگویید: «این محصول همین حالا روی سرور در حال اجرا است.»
- UI: `http://193.162.129.58:3000`
- انتظار: صفحه ورود Rivar
- ادعا: محصول deploy شده است
- جایگزین: `curl http://127.0.0.1:8000/health`

### ۲. کانتینرها — ۲ دقیقه

```bash
cd /root/pdss && docker compose ps
```

- انتظار: backend/frontend/postgres Up
- ادعا: استقرار Docker Compose
- فایل: `docker-compose.yml`

### ۳. سلامت Backend — ۱ دقیقه

```bash
curl -sS http://127.0.0.1:8000/health
```

- انتظار: `product=Rivar`, `producer=Corbit`, `version=1.0.0-rc1`
- ادعا: هویت محصول در runtime

### ۴. ورود زنده — ۲ دقیقه

- UI: `/login` با `admin` / `admin123`
- انتظار: ورود به داشبورد
- ادعا: احراز هویت JWT
- جایگزین: `POST /auth/login`

### ۵. داشبورد — ۳ دقیقه

- UI: `/dashboard` (از منو، نه deep link اگر 404 شد)
- انتظار: نمای نقدینگی
- ادعا: داشبورد نقدینگی پیاده شده
- API: `/dashboard/summary`, `/dashboard/cashflow`

### ۶. فهرست پروژه — ۲ دقیقه

- UI: `/projects`
- انتظار: پروژه‌های `DEMO_IT_1405_...`
- ادعا: مدیریت پروژه
- نکته: ۳۰ پروژه IT ۱۴۰۵

### ۷. یک پروژه IT — ۲ دقیقه

- باز کنید: Data Center Modernization یا Core Network Upgrade
- انتظار: اولویت، بودجه IRR، ورود به اقلام
- ادعا: سبد تأمین پروژه‌ای واقعی

### ۸. قلم پایه و زیرقلم — ۳ دقیقه

- UI: `/items-master`
- یک Rack Server را باز کنید
- انتظار: شرکت/مدل/دسته و لیست CPU، RAM، PSU و غیره
- ادعا: کاتالوگ و تجزیه قطعه
- API: `/items-master/{id}/subitems`

### ۹. شکست قلم پروژه — ۳ دقیقه

- UI: اقلام همان پروژه
- انتظار: مقدار، تاریخ تحویل، پیوند به قلم پایه
- ادعا: تقاضا روی پروژه ثبت می‌شود

### ۱۰. اقلام نهایی‌شده — ۳ دقیقه

- اقلامی که Finalize شده‌اند را نشان دهید
- در صورت نیاز eligibility یک قلم باز را نشان دهید
- ادعا: ارسال به تأمین فقط با شرایط کامل
- API: `/items/{id}/procurement-eligibility`
- جایگزین: کد `procurement_eligibility_service.py`

### ۱۱. تخصیص کارشناس — ۳ دقیقه

- با `admin` یا `pmo1` تب Assignments را باز کنید
- سپس با `proc1` «اقلام من» را نشان دهید
- انتظار: تخصیص بین `proc1` و `proc2`
- ادعا: کار تأمین قابل تخصیص و قابل مشاهده است
- API: `/procurement-assignments/assigned-items`

### ۱۲. تأمین‌کنندگان متمایز — ۲ دقیقه

- UI: `/suppliers`
- دو تأمین‌کننده با ضعف/قوت متفاوت را بخوانید
- ادعا: گزینه تأمین فقط نام نیست؛ شرایط فرق دارد

### ۱۳. گزینه‌های تأمین — ۳ دقیقه

- UI: `/procurement` روی یک قلم نهایی
- انتظار: ۲ تا ۴ گزینه با قیمت/سرعت/پرداخت متفاوت
- ادعا: مقایسه گزینه برای بهینه‌سازی
- API: `/procurement/options`

### ۱۴. پوشش بسته — ۳ دقیقه

- Coverage modal یا `/packages/coverage/{id}`
- یک FULL و یک PARTIAL/incomplete را نشان دهید
- ادعا: سیستم پوشش کامل و ناقص را می‌فهمد

### ۱۵. رد lock پوشش ناقص — ۳ دقیقه

- اول `GET /config/feature-flags` را نشان دهید
- اگر flagها خاموش‌اند، صادقانه بگویید: «منطق در کد و تست هست؛ روی این runtime پیش‌فرض اجباری نیست.»
- شاهد جایگزین: `validate_package_coverage_for_lock` و `test_phase5_decision_lock_coverage.py`
- ادعا نکنید که همین لحظه UI حتماً lock ناقص را رد می‌کند مگر flag روشن باشد

### ۱۶. lock موفق پوشش کامل — ۲ دقیقه

- اگر یک تصمیم کامل ساخته‌اید، finalize را نشان دهید
- وگرنه مسیر `/decisions` و کد `POST /decisions/finalize` را نشان دهید
- دمو ۱۴۰۵ تصمیم‌ها را از پیش lock نکرده تا بهینه‌سازی قابل نمایش بماند

### ۱۷. مسیر بهینه‌سازی — ۵ دقیقه

- UI: `/optimization-enhanced`
- `GET /finance/solver-info` یا انتخاب solver
- در صورت زمان، یک run کوچک
- ادعا: انتخاب گزینه با حل‌کننده محدودیت، نه فقط گزارش
- فایل: `optimization_engine_enhanced.py`
- نگویید PuLP

### ۱۸. برنامه تأمین — ۲ دقیقه

- UI: `/procurement-plan`
- اگر خالی است بگویید: «این صفحه تصمیم‌های LOCKED را نشان می‌دهد؛ دمو فعلی روی آمادگی بهینه‌سازی است.»
- API: `/procurement-plan/`

### ۱۹–۲۲. تحویل، پذیرش PM، فاکتور، پرداخت تأمین

- اگر تصمیم قفل‌شده دارید، همان صفحه plan و تب Finance را بروید
- اگر ندارید: API و مدل را نشان دهید، ادعا نکنید داده دمو همه این مراحل را پر کرده
- مسیرها: `confirm-delivery`, `accept-delivery`, `/api/invoice-payment`, `/supplier-payments`

### ۲۳. اثر نقدینگی/گزارش — ۳ دقیقه

- Dashboard و `/reports`
- بودجه Mehr 1405 را به‌عنوان پنجره کمبود بگویید
- ادعا: مالی به تأمین وصل است

### ۲۴. ممیزی — ۲ دقیقه

- UI: `/audit-logs` با admin
- انتظار: LOGIN و اقدامات
- ادعا: قابلیت ردیابی

### ۲۵. ساختار کد — ۳ دقیقه

- `backend/app/main.py` و `frontend/src/App.tsx`
- بگویید: «ماژول‌ها جدا هستند: پروژه، تأمین، بسته، مالی، بهینه‌سازی.»

### ۲۶. تست‌ها — ۲ دقیقه

- پوشه `backend/tests/`
- صادقانه: suite کامل به‌خاطر import phase13f در collection قطع می‌شود
- تست‌های پوشش و تخصیص را نام ببرید

### ۲۷. بسته انتشار — ۱ دقیقه

- `release_packages/corbit-rivar-rc1/`
- `RELEASE_NOTES.md` و `KNOWN_LIMITATIONS.md`

### ۲۸. ایمنی backup/update — ۱ دقیقه

- `scripts/windows/deployment/backup_database.bat`
- بگویید volume دیتابیس جدا است و `down -v` ممنوع است

### ۲۹. محدودیت‌ها — ۲ دقیقه

از چک‌لیست جلسه بخوانید. بیش‌ادعا نکنید.

## اگر UI قطع شد

1. Health و OpenAPI
2. Login API
3. یک GET با token: `/projects` یا `/procurement/items-with-details`
4. `--mode verify` دمو
5. فایل کد مربوط به همان ادعا

## جمله پایانی پیشنهادی

«Rivar یک سامانه تصمیم‌یار تأمین پروژه‌ای است که از تعریف تقاضا تا گزینه تأمین، پوشش بسته، بهینه‌سازی و اثر نقدینگی را روی داده واقعی همین سرور نشان می‌دهد. نسخه فعلی pilot/RC است؛ بعضی کنترل‌ها مثل اجبار پوشش هنگام lock با feature flag مدیریت می‌شوند و ما آن را پنهان نمی‌کنیم.»
