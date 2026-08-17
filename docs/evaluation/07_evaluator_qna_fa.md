# پرسش و پاسخ احتمالی ارزیاب

برای هر پاسخ: جواب کوتاه، شاهد زنده، مسیر فایل/API.

## ۱. هویت و هدف محصول

**۱. این محصول چیست؟**  
پاسخ کوتاه: Rivar سامانه تصمیم‌یار تأمین پروژه‌ای و بهینه‌سازی نقدینگی ساخت Corbit است.  
شاهد: Login و `/health`.  
مرجع: `backend/app/app_metadata.py`, `backend/VERSION`.

**۲. چه مسئله‌ای را حل می‌کند؟**  
پاسخ کوتاه: انتخاب تأمین در سبد پروژه وقتی چند گزینه، چند قطعه، بودجه و زمان با هم برخورد می‌کنند.  
شاهد: یک پروژه دمو با چند گزینه.  
مرجع: `docs/evaluation/03_architecture_fa.md`.

**۳. نسخه فعلی چیست؟**  
پاسخ کوتاه: `1.0.0-rc1`، وضعیت pilot/RC.  
شاهد: `/health`.  
مرجع: `backend/VERSION`.

**۴. آیا محصول تمام‌شده تجاری است؟**  
پاسخ کوتاه: خیر؛ RC/پایلوت است و محدودیت‌های صریح دارد.  
شاهد: `KNOWN_LIMITATIONS.md`.  
مرجع: `release_packages/corbit-rivar-rc1/KNOWN_LIMITATIONS.md`.

## ۲. معماری و فناوری

**۵. معماری چیست؟**  
پاسخ کوتاه: React + FastAPI + PostgreSQL داخل Docker Compose.  
شاهد: `docker compose ps`.  
مرجع: `docker-compose.yml`.

**۶. API چه شکلی است؟**  
پاسخ کوتاه: REST JSON با OpenAPI.  
شاهد: `/openapi.json` حدود ۱۷۹ مسیر.  
مرجع: `backend/app/main.py`.

**۷. بهینه‌سازی با چیست؟**  
پاسخ کوتاه: Google OR-Tools. PuLP در dependencies هست ولی در کد استفاده نشده.  
شاهد: `GET /finance/solver-info` و فایل موتور.  
مرجع: `backend/app/optimization_engine_enhanced.py`.

**۸. چرا PostgreSQL؟**  
پاسخ کوتاه: داده رابطه‌ای سازمانی با قید و دوام روی volume.  
شاهد: سرویس postgres healthy.  
مرجع: `docker-compose.yml`.

## ۳. مالکیت و کد منبع

**۹. کد مال کیست / کجاست؟**  
پاسخ کوتاه: مخزن محصول روی شاخه `restart/sprint5f-fix2-runtime-ui-closure`.  
شاهد: `git rev-parse HEAD` روی سرور و محلی.  
مرجع: همین مخزن.

**۱۰. آیا کد روی سرور همان کد پذیرفته‌شده است؟**  
پاسخ کوتاه: بله روی همان شاخه 5F-Fix-2. HEAD گیت سرور `ad55a73` است و چند commit سندی/دمو عقب‌تر از workspace است.  
شاهد: `git log` دو طرف.  
مرجع: `docs/evaluation/00_current_runtime_and_source_state.md`.

**۱۱. نقطه ورود برنامه کجاست؟**  
پاسخ کوتاه: Backend `app.main:app`؛ Frontend `src/index.tsx` و `App.tsx`.  
شاهد: باز کردن همین فایل‌ها.  
مرجع: `backend/Dockerfile`, `frontend/src/App.tsx`.

## ۴. پایگاه داده و مدل

**۱۲. موجودیت‌های اصلی کدام‌اند؟**  
پاسخ کوتاه: پروژه، قلم پایه، زیرقلم، قلم پروژه، تأمین‌کننده، گزینه، بسته، تصمیم، بودجه، فاکتور، پرداخت، ممیزی.  
شاهد: `models.py`.  
مرجع: `backend/app/models.py`.

**۱۳. داده دمو جدا از داده سیستم است؟**  
پاسخ کوتاه: بله با پیشوند `DEMO_IT_1405_` و cleanup فقط همین مجموعه.  
شاهد: `--mode verify`.  
مرجع: `backend/scripts/create_it_procurement_demo_1405.py`.

**۱۴. تاریخ‌ها شمسی‌اند یا میلادی؟**  
پاسخ کوتاه: کسب‌وکار جلالی ۱۴۰۵ است؛ ذخیره دیتابیس میلادی است.  
شاهد: توضیحات اسکریپت دمو.  
مرجع: همان اسکریپت و `docs/restart-audit/32_it_demo_data_1405_feed_report.md`.

## ۵. امنیت و دسترسی

**۱۵. ورود چطور کار می‌کند؟**  
پاسخ کوتاه: JWT Bearer بعد از بررسی رمز.  
شاهد: Login زنده.  
مرجع: `backend/app/auth.py`.

**۱۶. نقش‌ها چیست؟**  
پاسخ کوتاه: admin، pmo، pm، procurement، finance.  
شاهد: ورود با چند کاربر.  
مرجع: `backend/app/seed_data.py`.

**۱۷. RBAC کامل است؟**  
پاسخ کوتاه: زیرساخت نقش/مجوز پیاده شده؛ اجبار سراسری پیش‌فرض خاموش است. مدل دوگانه است.  
شاهد: `/users-access` و `GET /config` مربوط به flagها.  
مرجع: `backend/app/config.py`, `rbac_service.py`.

**۱۸. ممیزی دارید؟**  
پاسخ کوتاه: بله؛ لاگ ورود و صفحه audit برای admin.  
شاهد: `/audit-logs`.  
مرجع: `backend/app/routers/audit.py`.

## ۶. گردش تأمین

**۱۹. جریان تأمین چیست؟**  
پاسخ کوتاه: پروژه → قلم → نهایی‌سازی → تخصیص → گزینه/بسته → بهینه‌سازی → تصمیم → اجرا.  
شاهد: صفحات همین ترتیب.  
مرجع: `docs/evaluation/03_architecture_fa.md`.

**۲۰. چه چیزی جلوی ارسال ناقص به تأمین را می‌گیرد؟**  
پاسخ کوتاه: eligibility: مقدار، تاریخ تحویل، قیمت فروش.  
شاهد: تلاش finalize روی قلم ناقص یا API eligibility.  
مرجع: `procurement_eligibility_service.py`.

**۲۱. تخصیص کارشناس کجاست؟**  
پاسخ کوتاه: در تأمین، با دامنه پروژه یا قلم.  
شاهد: تب Assignments و کاربر `proc1`.  
مرجع: `backend/app/routers/procurement_assignments.py`.

## ۷. تصمیم و بهینه‌سازی

**۲۲. بهینه‌سازی چه ورودی می‌گیرد؟**  
پاسخ کوتاه: اقلام نهایی، گزینه‌های تأمین، بودجه، قیود زمان/هزینه.  
شاهد: صفحه Optimization Enhanced.  
مرجع: `finance.py`, موتور enhanced.

**۲۳. خروجی بهینه‌سازی چیست؟**  
پاسخ کوتاه: پیشنهاد انتخاب گزینه و run قابل ذخیره؛ قفل جداست.  
شاهد: لیست optimization runs.  
مرجع: `optimization_runs`, `/decisions`.

**۲۴. آیا همه تصمیم‌های دمو از قبل قفل شده‌اند؟**  
پاسخ کوتاه: خیر؛ دمو ۱۴۰۵ برای ورود به بهینه‌سازی است نه بستن کل سبد.  
شاهد: `--mode verify` و نبود تصمیم lock انبوه.  
مرجع: اسکریپت دمو.

## ۸. بسته و پوشش

**۲۵. زیرقلم یعنی چه؟**  
پاسخ کوتاه: قطعات تشکیل‌دهنده یک تجهیز.  
شاهد: Rack Server در Items Master.  
مرجع: `ItemSubItem`.

**۲۶. بسته کامل و جزئی چیست؟**  
پاسخ کوتاه: FULL همه نیاز را می‌دهد؛ PARTIAL بخشی را.  
شاهد: coverage modal.  
مرجع: `ProcurementPackage.package_type`.

**۲۷. lock پوشش ناقص رد می‌شود؟**  
پاسخ کوتاه: در کد بله، اگر هر دو feature flag روشن باشند. روی این runtime پیش‌فرض خاموش است.  
شاهد: flag API + تابع + تست.  
مرجع: `package_service.py` خطوط ۴۳۷–۴۵۴.

## ۹. مالی و نقدینگی

**۲۸. فاکتور و دریافت کجاست؟**  
پاسخ کوتاه: تب Invoice & Payment در Finance و API `/api/invoice-payment`.  
شاهد: همان صفحه.  
مرجع: `invoice_payment_simple.py`.

**۲۹. پرداخت به تأمین‌کننده جدا است؟**  
پاسخ کوتاه: بله، `supplier_payments`.  
شاهد: API `/supplier-payments`.  
مرجع: `backend/app/routers/supplier_payments.py`.

**۳۰. داشبورد از کجا تغذیه می‌شود؟**  
پاسخ کوتاه: رویداد نقدینگی و بودجه دوره‌ای.  
شاهد: Dashboard.  
مرجع: `backend/app/routers/dashboard.py`.

**۳۱. کمبود بودجه دمو کجاست؟**  
پاسخ کوتاه: مهر ۱۴۰۵.  
شاهد: verify دمو.  
مرجع: اسکریپت دمو، `budget_data`.

## ۱۰. ممیزی‌پذیری

**۳۲. چطور ثابت می‌کنید کار کاربر ثبت می‌شود؟**  
پاسخ کوتاه: یک بار login کنید و audit را باز کنید.  
شاهد: `/audit-logs`.  
مرجع: `log_audit` در login.

**۳۳. آیا همه اقدامات ممیزی می‌شوند؟**  
پاسخ کوتاه: خیر؛ ورود و بسیاری عملیات هست، ادعای پوشش صددرصدی نکنید.  
شاهد: جدول `audit_logs` و کد.  
مرجع: `models.py` کلاس `AuditLog`.

## ۱۱. استقرار و نگهداری

**۳۴. چطور نصب/اجرا می‌شود؟**  
پاسخ کوتاه: Docker Compose؛ installer جدا هم هست.  
شاهد: `docker compose ps`.  
مرجع: `docker-compose.yml`, `deployment/rivar-installer/`.

**۳۵. اگر کانتینر حذف شود داده می‌ماند؟**  
پاسخ کوتاه: بله، مگر volume پاک شود. `down -v` ممنوع است.  
شاهد: تعریف volume.  
مرجع: `docker-compose.yml`.

**۳۶. به‌روزرسانی ایمن دارید؟**  
پاسخ کوتاه: اسکریپت backup/update هست؛ دکمه rollback داخل UI نیست.  
شاهد: پوشه `scripts/*/deployment`.  
مرجع: همان.

## ۱۲. تست و کیفیت

**۳۷. تست دارید؟**  
پاسخ کوتاه: بله، مجموعه pytest فازبندی‌شده.  
شاهد: `backend/tests/`.  
مرجع: `requirements.txt`.

**۳۸. الان همه تست‌ها سبز است؟**  
پاسخ کوتاه: خیر. collection روی `financial_projections` خطا می‌دهد.  
شاهد: `pytest tests -q`.  
مرجع: `backend/tests/test_phase13f_financial_projection_engine.py`.

**۳۹. ساخت frontend موفق است؟**  
پاسخ کوتاه: بله، با هشدار ESLint موجود.  
شاهد: `npm run build`.  
مرجع: `frontend/package.json`.

## ۱۳. محدودیت و نقشه راه

**۴۰. چه چیزی هنوز کامل نیست؟**  
پاسخ کوتاه: اجبار سراسری RBAC، lock پوشش به‌صورت پیش‌فرض، router تصویر مالی جدا، نرخ ارز جدا، برند در نام‌های قدیمی، deep-link SPA.  
شاهد: این بسته ارزیابی.  
مرجع: ماتریس قابلیت.

**۴۱. آیا قابلیت‌های آینده را هم ادعا می‌کنید؟**  
پاسخ کوتاه: خیر. فقط آنچه الان قابل نمایش است.  
شاهد: تفکیک implemented/partial در ماتریس.

## ۱۴. تفاوت با اکسل / فرآیند دستی

**۴۲. چرا اکسل کافی نیست؟**  
پاسخ کوتاه: اکسل قفل پوشش، تخصیص نقش، حل بهینه‌سازی و ممیزی متمرکز ندارد.  
شاهد: eligibility و solver زنده.  
مرجع: سرویس eligibility و موتور OR-Tools.

**۴۳. چند کاربر همزمان چطور؟**  
پاسخ کوتاه: داده مرکزی در PostgreSQL است و دسترسی با نقش جدا می‌شود.  
شاهد: ورود `proc1` در برابر `finance1`.  
مرجع: `Layout.tsx`, نقش‌ها.

## ۱۵. تفاوت با ERP / حسابداری عمومی

**۴۴. آیا Rivar ERP است؟**  
پاسخ کوتاه: خیر. تمرکز آن تصمیم تأمین و نقدینگی پروژه است، نه انبار کامل یا دفترکل.  
شاهد: ماژول‌های موجود در `main.py`.  
مرجع: لیست routerها.

**۴۵. آیا جایگزین نرم‌افزار حسابداری است؟**  
پاسخ کوتاه: خیر. فاکتور و پرداخت مرتبط با تصمیم تأمین دارد، نه حسابداری کامل.  
شاهد: محدوده `/api/invoice-payment`.  
مرجع: `models_invoice_payment.py`.

**۴۶. ارزش دانش‌بنیان کجاست؟**  
پاسخ کوتاه: مدل پوشش بسته + حل بهینه‌سازی مقید + اتصال نتیجه به نقدینگی، روی داده واقعی.  
شاهد: coverage + solver + dashboard.  
مرجع: `package_service.py`, `optimization_engine_enhanced.py`, `dashboard.py`.
