# نقشه مخزن و نقش هر بخش

این سند برای نشان دادن ساختار واقعی کد در جلسه است. مسیرها به انگلیسی مانده‌اند.

## نمای کلی مخزن

```text
cahs_flow_project/
  backend/                 API، مدل‌ها، سرویس‌ها، تست، اسکریپت دمو
  frontend/                UI React
  docker-compose.yml       اجرای سه‌سرویسی توسعه/دمو
  deployment/rivar-installer/  نصب، verify، deploy اسپرینت
  docs/restart-audit/      اسناد استقرار و بستن اسپرینت
  docs/release/            یادداشت انتشار، UAT، محدودیت‌ها
  docs/evaluation/         همین بسته ارزیابی
  release_packages/corbit-rivar-rc1/  بسته RC1
  scripts/                 backup/update ویندوز و لینوکس
```

## Backend

### نقاط ورود و هسته

| مسیر | نقش |
| --- | --- |
| `backend/app/main.py` | ساخت FastAPI، ثبت routerها، `GET /health`, `GET /`، seed RBAC در startup |
| `backend/app/app_metadata.py` | نام `Rivar` و تولیدکننده `Corbit` |
| `backend/VERSION` | `1.0.0-rc1` |
| `backend/app/database.py` | engine async و session |
| `backend/app/config.py` | JWT، CORS، feature flagها |
| `backend/app/auth.py` | ساخت/خواندن JWT، `get_current_user`، نقش و مجوز |
| `backend/app/models.py` | مدل دامنه اصلی |
| `backend/app/models_invoice_payment.py` | `Invoice` و `Payment` |
| `backend/app/schemas.py` | قراردادهای Pydantic |
| `backend/app/crud.py` | عملیات رایج شامل نهایی‌سازی قلم و audit |
| `backend/app/routers/` | لایه HTTP |
| `backend/app/services/` | منطق کسب‌وکار |
| `backend/app/validators/` | اعتبارسنجی بسته/ارجاع |
| `backend/tests/` | آزمون‌های فازبندی |
| `backend/scripts/` | دمو، smoke، verify |

### Routerها و نمایش زنده

| فایل | پیشوند | ماژول کسب‌وکار | نمایش زنده پیشنهادی |
| --- | --- | --- | --- |
| `auth.py` | `/auth` | ورود و هویت | Login، `/auth/me` |
| `access_control.py` | `/access-control` | نقش و مجوز | صفحه Users & Access |
| `users.py` | `/users` | کاربران | تب کاربران |
| `projects.py` | `/projects` | پروژه‌ها و پوشش تجمیعی | لیست پروژه، coverage-summary |
| `items_master.py` | `/items-master` | کاتالوگ و زیرقلم | Items Master |
| `items.py` | `/items` | اقلام پروژه و ارسال به تأمین | Finalize، eligibility |
| `phases.py` | `/phases` | فاز پروژه | دیالوگ فاز در پروژه |
| `weights.py` | `/weights` | وزن عوامل تصمیم | صفحه Weights |
| `decisions.py` | `/decisions` | پیشنهاد/قفل تصمیم | Decisions، finalize |
| `delivery_options.py` | `/delivery-options` | زمان و قیمت فروش تحویل | گزینه‌های تحویل قلم |
| `procurement.py` | `/procurement` | گزینه‌های تأمین | صفحه Procurement |
| `procurement_assignments.py` | مسیر کامل | تخصیص کارشناس | تب Assignments |
| `procurement_financials.py` | مسیر کامل | روش پرداخت و هزینه | Payment Methods |
| `procurement_plan.py` | `/procurement-plan` | تحویل، پذیرش PM، فاکتور عملیاتی | Procurement Plan |
| `finance.py` | `/finance` | بودجه و اجرای بهینه‌سازی | Finance + Optimization |
| `excel.py` | `/excel` | ورود/خروج اکسل | Import/Export اقلام |
| `dashboard.py` | `/dashboard` | نقدینگی | Dashboard |
| `analytics.py` | `/analytics` | EVA، ریسک، پیش‌بینی | Analytics |
| `reports.py` | `/reports` | گزارش و خروجی اکسل | Reports |
| `files.py` | `/files` | پیوست قلم | آپلود در اقلام پروژه |
| `currencies.py` | `/currencies` | ارز و نرخ | تب Currency در Finance |
| `brs_api.py` | `/brs-api` | خوراک ارز خارجی | وابسته به سرویس بیرونی |
| `suppliers.py` | `/suppliers` | تأمین‌کنندگان | Suppliers |
| `invoice_payment_simple.py` | `/api/invoice-payment` | فاکتور و دریافت | تب Invoice & Payment |
| `supplier_payments.py` | `/supplier-payments` | پرداخت به تأمین‌کننده | از مسیر مالی/تصمیم |
| `audit.py` | `/audit-logs` | ممیزی | Audit Logs (admin) |
| `config.py` | `/config` | feature flag | `GET /config/feature-flags` |
| `packages.py` | `/packages` | بسته، پوشش، ارسال به بهینه‌سازی | Package wizard / coverage |

Router موجود ولی سوارنشده: `invoice_payment.py`.  
Router موجود ولی غیرفعال: `exchange_rates.py` (توضیح در `main.py`: Pydantic recursion).

### سرویس‌های مهم

| فایل | کار |
| --- | --- |
| `procurement_eligibility_service.py` | آیا قلم قابل ارسال به تأمین است |
| `procurement_assignment_service.py` | تخصیص کارشناس |
| `package_service.py` | پوشش و `validate_package_coverage_for_lock` |
| `package_combination_service.py` | ترکیب بسته و submission |
| `procurement_financials_service.py` | هزینه فرود و قرارداد زمان‌بندی |
| `optimization_budget_service.py` | تحلیل بودجه سناریو |
| `optimization_rollback_service.py` | rollback ارسال به بهینه‌سازی |
| `atomic_optimization_candidate_service.py` | ساخت کاندید اتمی |
| `financial_projection_service.py` | موتور تصویر مالی؛ به سرویس پوشش کاندید ارجاع می‌دهد که فایلش در این درخت نیست |
| `rbac_service.py` | بذر و مجوز مؤثر |
| `audit_service.py` | ثبت عملیات فاز ۳ |
| `cashflow_sync_service.py` | همگام‌سازی فاکتور/پرداخت با رویداد نقدینگی |

موتور بهینه‌سازی بیرون از `services/`: `backend/app/optimization_engine.py` و `optimization_engine_enhanced.py`.

## Frontend

### ورود و پوسته

| مسیر | نقش |
| --- | --- |
| `frontend/src/index.tsx` | `BrowserRouter` |
| `frontend/src/App.tsx` | مسیرها، تم RTL/LTR، عنوان Rivar \| Corbit |
| `frontend/src/contexts/AuthContext.tsx` | JWT در localStorage |
| `frontend/src/components/ProtectedRoute.tsx` | اجبار ورود |
| `frontend/src/components/Layout.tsx` | منو بر اساس نقش/مجوز |
| `frontend/src/services/api.ts` | کلاینت axios و ماژول‌های API |
| `frontend/src/utils/appIdentity.ts` | هویت محصول و نسخه از `/health` |
| `frontend/src/i18n/` | en/fa |

### صفحات و فرآیند

| مسیر UI | صفحه | فرآیند | API اصلی |
| --- | --- | --- | --- |
| `/login` | `LoginPage` | ورود | `/auth/login`, `/auth/me` |
| `/dashboard` | `DashboardPage` | نقدینگی | `dashboardAPI` |
| `/projects` | `ProjectsPage` | تعریف پروژه | `projectsAPI` |
| `/items-master` | `ItemsMasterPage` | کاتالوگ و زیرقلم | `itemsMasterAPI` |
| `/projects/:id/items` | `ProjectItemsPage` | اقلام پروژه و نهایی‌سازی | `itemsAPI`, `packagesAPI` |
| `/procurement` | `ProcurementPage` | گزینه، بسته، تخصیص | `procurementAPI`, `packagesAPI`, `procurementAssignmentsAPI` |
| `/procurement-plan` | `ProcurementPlanPage` | تحویل و پذیرش | `procurementPlanAPI` |
| `/optimization-enhanced` | `OptimizationPage_enhanced` | اجرا و قفل تصمیم | `financeAPI`, `decisionsAPI` |
| `/optimization` | `OptimizationPage` | مسیر قدیمی؛ در منو نیست | `financeAPI` |
| `/finance` | `FinancePage` | بودجه، ارز، فاکتور | `financeAPI`, `invoicePaymentAPI` |
| `/payment-methods` | `PaymentMethodsPage` | روش پرداخت | `procurementFinancialsAPI` |
| `/suppliers` | `SuppliersPage` | تأمین‌کننده | `suppliersAPI` |
| `/decisions` | `FinalizedDecisionsPage` | تصمیم‌ها | `decisionsAPI` |
| `/analytics` | `AnalyticsDashboardPage` | EVA/ریسک | `analyticsAPI` |
| `/reports` | `ReportsPage` | گزارش | `reportsAPI` |
| `/audit-logs` | `AuditLogsPage` | ممیزی | `auditLogsAPI` |
| `/users-access` | `UsersAccessControlPage` | کاربر و نقش | `usersAPI`, `accessControlAPI` |
| `/weights` | `WeightsPage` | وزن تصمیم | `weightsAPI` |

محافظ مسیر جدا: `ProjectItemsRoute`, `UsersAccessControlRoute`, `PaymentMethodsRoute`. بقیه صفحات بیشتر با مخفی‌کردن منو و 403 بک‌اند محافظت می‌شوند.

## استقرار و انتشار

| مسیر | نقش |
| --- | --- |
| `docker-compose.yml` | اجرای فعلی `/root/pdss` |
| `deployment/rivar-installer/install.sh` | نصب/ارتقا |
| `deployment/rivar-installer/verify.sh` | بررسی runtime |
| `deployment/rivar-installer/docker-compose.rivar-demo.yml` | استک دمو جدا |
| `scripts/windows/deployment/backup_database.bat` | پشتیبان |
| `scripts/windows/deployment/update-deployed-platform.bat` | به‌روزرسانی |
| `release_packages/corbit-rivar-rc1/` | بسته RC1 |
| `docs/release/` | یادداشت انتشار و UAT |
| `docs/restart-audit/` | شواهد بستن اسپرینت و استقرار |

## آنچه در جلسه از کد نشان داده شود

1. `backend/app/main.py` — ثبت ماژول‌ها و health
2. `backend/app/models.py` — مدل دامنه
3. `frontend/src/App.tsx` — مسیرهای محصول
4. `backend/app/optimization_engine_enhanced.py` — حل‌کننده
5. `backend/app/services/package_service.py` — پوشش و lock
6. `docker-compose.yml` — سه سرویس
