# ماتریس قابلیت و شاهد

وضعیت‌ها فقط از کد و runtime فعلی آمده‌اند.

راهنمای وضعیت:

- `implemented`: در کد هست و مسیر نمایش زنده دارد
- `partial`: پیاده شده ولی ناقص، flag-خورده، یا UI کامل نیست
- `documented only`: در سند هست، در کد سوار نشده
- `not found`: در این درخت پیدا نشد

| ادعا / قابلیت | وضعیت | محل نمایش زنده در UI | API / ماژول | مدل/دیتابیس | تست/اسکریپت | دیتای دمو | محدودیت / نکته |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ۱. مدیریت کاربران و ورود | implemented | `/login`, `/users-access` | `POST /auth/login`, `/users` | `users` | تست‌های auth/RBAC، seed_data | کاربران بذر | JWT؛ رمز دمو فقط برای جلسه |
| ۲. نقش‌ها و دسترسی‌ها | partial | `/users-access` تب نقش | `/access-control/*`, `rbac_service` | `roles`, `permissions`, `user_roles` | تست‌های Sprint 5B/5C | نقش‌های بذر | enforcement سراسری پیش‌فرض خاموش؛ نقش قدیمی هنوز فعال است |
| ۳. مدیریت پروژه‌ها | implemented | `/projects` | `/projects` | `projects`, `project_assignments` | تست پروژه | ۳۰ پروژه `DEMO_IT_1405_` | — |
| ۴. تعریف اقلام پروژه | implemented | `/projects/:id/items` | `/items` | `project_items` | تست eligibility | ۹۰۰ قلم | — |
| ۵. اطلاعات پایه اقلام | implemented | `/items-master` | `/items-master` | `items_master` | تست master data | ۲۶ قلم پایه | — |
| ۶. sub-item/component | implemented | زیرقلم در Items Master و اقلام پروژه | `/items-master/{id}/subitems` | `item_subitems`, `project_item_subitems` | تست بسته/پوشش | ۱۳۱ زیرقلم کاتالوگ | حدود ۸۱٪ اقلام پایه تجزیه شده‌اند |
| ۷. ارسال اقلام نهایی‌شده به تأمین | implemented | Finalize در اقلام پروژه | `PUT /items/{id}/finalize`, eligibility | `project_items.is_finalized` | `test_project_item_procurement_eligibility.py` | ۲۷۰ قلم نهایی | بدون گزینه تحویل/قیمت، finalize رد می‌شود |
| ۸. تخصیص کارشناس تأمین | implemented | تب Assignments در `/procurement` | `/procurement-assignments` | `procurement_assignments` | تست Sprint 5D/5E/5F | ۲۷۰ تخصیص `proc1`/`proc2` | فقط اقلام نهایی در دامنه تخصیص |
| ۹. مدیریت تأمین‌کنندگان | implemented | `/suppliers` | `/suppliers` | `suppliers` | تست/اسکریپت دمو | ۱۲ تأمین‌کننده متمایز | — |
| ۱۰. گزینه‌های تأمین | implemented | `/procurement` | `/procurement/options` | `procurement_options` | fixture Sprint 4A، دمو ۱۴۰۵ | ۶۴۸ گزینه | قرارداد زمان‌بندی در سرویس مالی |
| ۱۱. package کامل/جزئی | implemented | Package wizard / لیست بسته | `/packages` | `procurement_packages` | دمو + تست پوشش | ۶۴۸ بسته FULL/PARTIAL | — |
| ۱۲. محاسبه coverage | implemented | Coverage modal | `GET /packages/coverage/{item_id}`, `/projects/{id}/coverage-summary` | `package_subitems` | `package_service` | ۳۴۰۱ ردیف پوشش | شامل موارد ناقص عمدی |
| ۱۳. جلوگیری از lock در coverage ناقص | partial | Optimization/Decisions اگر flag روشن باشد | `validate_package_coverage_for_lock`, `POST /decisions/finalize` | `finalized_decisions` + بسته | `test_phase5_decision_lock_coverage.py` | بسته‌های incomplete دمو | **هر دو flag باید روشن باشند**؛ در compose پیش‌فرض خاموش |
| ۱۴. lock/finalize در coverage کامل | partial | `/optimization-enhanced`, `/decisions` | `/decisions/finalize`, `/decisions/{id}/status` | `finalized_decisions.status` | همان تست‌ها + دمو RC8 قدیمی | دمو ۱۴۰۵ تصمیم‌ها را قفل نکرده | دمو برای ورود به بهینه‌سازی است نه پرتفوی قفل‌شده |
| ۱۵. تصمیم‌سازی / optimization | implemented | `/optimization-enhanced` | `POST /finance/optimize-enhanced`, `/finance/solver-info` | `optimization_runs`, `optimization_results` | تست‌های phase12e | ۲۱۶ قلم آماده‌بهینه، ۱۰۸ submission | حل‌کننده OR-Tools است نه PuLP |
| ۱۶. برنامه تأمین | implemented | `/procurement-plan` | `/procurement-plan` | `finalized_decisions` فیلدهای تحویل | تست/صفحه plan | نیاز به تصمیم LOCKED | دمو ۱۴۰۵ عمداً تصمیم‌ها را lock نکرده |
| ۱۷. تأیید تحویل توسط تأمین | implemented | Procurement Plan | `POST /procurement-plan/{id}/confirm-delivery` | `procurement_confirmed_at` | کد `procurement_plan.py` | نیاز به تصمیم قفل‌شده | بدون تصمیم lock در دمو، با داده موجود یا ساخت یک تصمیم زنده نشان دهید |
| ۱۸. پذیرش تحویل توسط PM | implemented | Procurement Plan | `POST /procurement-plan/{id}/accept-delivery` | `is_accepted_by_pm`, `pm_accepted_at` | analytics از همین فیلد استفاده می‌کند | همان | — |
| ۱۹. ثبت invoice | implemented | تب Invoice در `/finance` | `/api/invoice-payment/invoices`, `enter-invoice` | `invoices` | `invoice_payment_simple.py` | پس از تصمیم | router کامل `invoice_payment.py` سوار نشده |
| ۲۰. payment-in / دریافت | implemented | همان تب | `/api/invoice-payment/payments` | `payments` | cashflow sync | پس از فاکتور | — |
| ۲۱. supplier payment | implemented | مسیر مالی/تصمیم | `/supplier-payments` | `supplier_payments` | router سوارشده | پس از تصمیم | — |
| ۲۲. cashflow events | implemented | Dashboard | `/dashboard/cashflow`, sync | `cashflow_events` | `cashflow_sync_service.py` | بودجه ۷ دوره دمو | رویداد کامل پس از فاکتور/پرداخت ساخته می‌شود |
| ۲۳. dashboard | implemented | `/dashboard` | `/dashboard/summary`, `/cashflow` | تجمیع رویداد/بودجه | صفحه + API | دیتای دمو + بودجه | ورود از `/` |
| ۲۴. reports | implemented | `/reports` | `/reports/`, `/export/excel` | تجمیع چند جدول | صفحه Reports | دیتای دمو | — |
| ۲۵. analytics | implemented | `/analytics` | `/analytics/eva/{id}` و portfolio | تصمیم و پذیرش PM | صفحه Analytics | بهتر با تصمیم قفل‌شده | — |
| ۲۶. audit logs | implemented | `/audit-logs` | `GET /audit-logs/` | `audit_logs` | login audit | ورود admin لاگ می‌سازد | فقط admin |
| ۲۷. Docker deployment | implemented | ترمینال | `docker compose ps` | volumeها | `docker-compose.yml` | استک زنده | سه سرویس healthy |
| ۲۸. backup/update safety | partial | اسناد و اسکریپت، نه دکمه UI | اسکریپت‌های `scripts/*/deployment` | volume دیتابیس | `docs/restart-audit/03_run_and_deployment.md` | — | rollback خودکار محصول در UI نیست |
| ۲۹. demo dataset tooling | implemented | ترمینال | `create_it_procurement_demo_1405.py` | ردیف‌های `DEMO_IT_1405_` | `--mode verify` | همین دیتاست | cleanup فقط همین پیشوند را پاک می‌کند |
| ۳۰. release package | implemented | پوشه بسته | `release_packages/corbit-rivar-rc1/` | — | `RELEASE_NOTES.md` | — | بسته‌های PDSS قدیمی را نشان ندهید |

## قابلیت‌های مرتبط که نباید بیش‌ادعا شوند

| موضوع | وضعیت واقعی |
| --- | --- |
| موتور تصویر مالی جدا (`financial_projections` router) | not found در routers سوارشده؛ تست phase13f خطا می‌دهد |
| نرخ ارز جدا (`exchange_rates` router) | documented/disabled در `main.py`؛ بخشی داخل `/currencies` هست |
| استفاده از PuLP | not found در importها |
| قفل اجباری پوشش در runtime فعلی | partial / flag-off |
| برند کامل در همه اسکریپت‌ها و نام دیتابیس | partial |

## شاهد سریع برای ارزیاب

اگر UI یک ردیف را نشان نداد، به ترتیب این‌ها را باز کنید:

1. همان API با token در مرورگر/curl
2. مدل در `backend/app/models.py`
3. تست هم‌نام در `backend/tests/`
4. `--mode verify` دمو
5. لاگ `docker compose logs backend --tail 50`
