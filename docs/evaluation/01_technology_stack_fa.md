# پشته فناوری Rivar

همه موارد زیر از فایل‌های فعلی مخزن استخراج شده‌اند. اگر کتابخانه‌ای فقط در dependencies آمده و در کد استفاده نشده، صریحاً نوشته شده است.

## Backend

| موضوع | مقدار واقعی | مدرک |
| --- | --- | --- |
| زبان | Python 3.11 | `backend/Dockerfile` |
| چارچوب وب | FastAPI 0.104.1 + Uvicorn | `backend/requirements.txt`, `backend/app/main.py` |
| معماری API | REST JSON، OpenAPI خودکار | `GET /openapi.json`، `app = FastAPI(...)` در `backend/app/main.py` |
| ORM / دسترسی داده | SQLAlchemy 2.0 async + asyncpg | `backend/requirements.txt`, `backend/app/database.py` |
| مهاجرت | Alembic در dependencies؛ بسیاری از تغییرات با SQL افزایشی در `backend/*.sql` | `backend/requirements.txt`, فایل‌های `backend/add_*.sql` |
| احراز هویت | JWT Bearer، الگوریتم HS256، انقضای ۳۰ دقیقه | `backend/app/auth.py`, `backend/app/config.py` |
| کنترل دسترسی | نقش قدیمی (`admin/pmo/pm/procurement/finance`) + RBAC کلید مجوز (Sprint 5B) | `backend/app/auth.py`, `backend/app/services/rbac_service.py`, `backend/app/routers/access_control.py` |
| بهینه‌سازی | Google OR-Tools (CP-SAT / GLOP / MIP) | `backend/app/optimization_engine.py`, `backend/app/optimization_engine_enhanced.py` |
| PuLP | فقط در requirements؛ `import pulp` در backend یافت نشد | `backend/requirements.txt` |
| اعتبارسنجی | Pydantic 2.5 | `backend/app/schemas.py` |
| تست | pytest + pytest-asyncio + httpx | `backend/requirements.txt`, `backend/tests/` |
| بسته‌های مهم دیگر | pandas, openpyxl, networkx, passlib/bcrypt, python-jose, aiosqlite | `backend/requirements.txt` |

ورود: `POST /auth/login` توکن Bearer برمی‌گرداند. نشست کوکی محور نیست.

پرچم `enable_permission_enforcement` پیش‌فرض خاموش است (`backend/app/config.py`). بخشی از مسیرها همچنان با نقش قدیمی و بخشی با کلید مجوز کنترل می‌شوند. در جلسه باید «مدل دوگانه» گفته شود، نه RBAC کامل همه‌جا.

## Frontend

| موضوع | مقدار واقعی | مدرک |
| --- | --- | --- |
| زبان | TypeScript / JavaScript | `frontend/package.json` (`typescript`) |
| چارچوب | React 18.2 | `frontend/package.json` |
| UI | MUI v5 + Emotion | `frontend/package.json` |
| نمودار | Recharts | `frontend/package.json`, صفحات Dashboard/Reports/Analytics |
| مسیریابی | react-router-dom 6 | `frontend/src/App.tsx`, `frontend/src/index.tsx` |
| ساخت | Create React App / `react-scripts` 5 | `frontend/package.json` — Vite نیست |
| HTTP | axios | `frontend/src/services/api.ts` |
| بومی‌سازی | i18next + `en.json` / `fa.json` | `frontend/src/i18n/` |
| RTL | با زبان فارسی `dir=rtl` و تم MUI | `frontend/src/components/LanguageSwitcher.tsx`, `frontend/src/App.tsx` |
| تاریخ جلالی | `date-fns-jalali` | `frontend/package.json` و صفحات مرتبط |
| Docker frontend | `node:18-alpine` و `npm start` | `frontend/Dockerfile` |

نام npm هنوز `procurement-dss-frontend` است. این محدودیت نام‌گذاری است، نه نبود برند در UI.

## پایگاه داده

| موضوع | مقدار واقعی | مدرک |
| --- | --- | --- |
| موتور | PostgreSQL 15 Alpine | `docker-compose.yml` |
| نام دیتابیس در compose | `procurement_dss` (نام قدیمی) | `docker-compose.yml` |
| استراتژی پایداری | volume با نام `postgres_data` | `docker-compose.yml` |
| جداول مهم | پروژه‌ها، اقلام پایه، اقلام پروژه، زیرقلم، تأمین‌کننده، گزینه تأمین، بسته، پوشش، تصمیم، بودجه، رویداد نقدینگی، فاکتور، پرداخت، تخصیص، RBAC، ممیزی | `backend/app/models.py`, `backend/app/models_invoice_payment.py` |

مدل‌های محوری: `Project`, `ItemMaster`, `ItemSubItem`, `ProjectItem`, `ProjectItemSubItem`, `ProcurementPackage`, `PackageSubItem`, `ProcurementOption`, `FinalizedDecision`, `BudgetData`, `CashflowEvent`, `Invoice`, `Payment`, `SupplierPayment`, `ProcurementAssignment`, `AuditLog`, `OptimizationRun`.

## استقرار

| موضوع | مقدار واقعی | مدرک |
| --- | --- | --- |
| ارکستراسیون | Docker Compose | `docker-compose.yml` |
| Backend | build از `./backend`، پورت ۸۰۰۰، bind-mount `./backend:/app` | `docker-compose.yml` |
| Frontend | build از `./frontend`، پورت ۳۰۰۰ | `docker-compose.yml` |
| Postgres | پورت ۵۴۳۲، volume دائمی | `docker-compose.yml` |
| فایل‌های آپلود | volume `uploads_data` | `docker-compose.yml` |
| نصب‌کننده دمو | `deployment/rivar-installer/` | `install.sh`, `verify.sh`, `docker-compose.rivar-demo.yml` |
| به‌روزرسانی | اسکریپت‌های ویندوز/لینوکس | `scripts/windows/deployment/`, `scripts/linux/deployment/` |
| پشتیبان | backup/restore ویندوز | `scripts/windows/deployment/backup_database.bat` |
| بسته RC1 | `release_packages/corbit-rivar-rc1/` | `README_RELEASE.md`, `RELEASE_NOTES.md`, `KNOWN_LIMITATIONS.md` |

بسته‌های قدیمی `installation_packages/PDSS_*` مربوط به نام قبلی محصول‌اند و نباید به‌عنوان بسته فعلی Rivar معرفی شوند.

## تست و تضمین کیفیت

| موضوع | مدرک |
| --- | --- |
| تست‌های backend | `backend/tests/` حدود ۲۸ ماژول فازبندی‌شده |
| Fixture تست | SQLite حافظه در `backend/tests/conftest.py` |
| Smokeهای اسپرینت | `backend/scripts/sprint5*_runtime_smoke.py`, `deployment/rivar-installer/verify.sh` |
| ساخت frontend | `npm run build` در `frontend/package.json` |
| دیتای دمو | `backend/scripts/create_it_procurement_demo_1405.py` |
| چک‌لیست انتشار | `docs/release/release_candidate_checklist.md`, `docs/release/product_smoke_test_checklist.md` |

محدودیت تست: `backend/tests/test_phase13f_financial_projection_engine.py` هنگام جمع‌آوری خطا می‌دهد چون `app.routers.financial_projections` وجود ندارد. این را نباید پنهان کرد.

## آنچه نباید ادعا شود

- استفاده عملی از PuLP
- Vite به‌عنوان ابزار ساخت
- nginx به‌عنوان سرویس فعلی frontend در `/root/pdss`
- RBAC سراسری اجباری روی همه APIها
- مهاجرت منحصراً Alembic بدون SQLهای دستی
