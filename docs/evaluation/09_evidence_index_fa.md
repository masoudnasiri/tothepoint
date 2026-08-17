# نمایه شاهد جلسه ارزیابی

فقط چیزهایی که الان وجود دارند. رمز `.env` نشان داده نشود.

## شاهد Runtime

| مورد | مقدار / دستور |
| --- | --- |
| Frontend | `http://193.162.129.58:3000` — از `/` وارد شوید |
| Backend | `http://193.162.129.58:8000` |
| Health | `http://193.162.129.58:8000/health` |
| OpenAPI | `http://193.162.129.58:8000/openapi.json` |
| مسیر سرور | `/root/pdss` |
| سرویس‌ها | `cd /root/pdss && docker compose ps` |
| کاربران دمو | `admin/admin123`, `pmo1/pmo123`, `pm1/pm123`, `proc1/proc123`, `finance1/finance123` |
| هویت runtime | `product=Rivar`, `producer=Corbit`, `version=1.0.0-rc1` |

## شاهد کد منبع

| موضوع | مسیر |
| --- | --- |
| ورود Backend | `backend/app/main.py` |
| هویت محصول | `backend/app/app_metadata.py`, `backend/VERSION` |
| مدل‌ها | `backend/app/models.py`, `backend/app/models_invoice_payment.py` |
| طرح‌ها | `backend/app/schemas.py` |
| احراز هویت | `backend/app/auth.py` |
| تنظیمات/flag | `backend/app/config.py` |
| CRUD | `backend/app/crud.py` |
| Routerها | `backend/app/routers/` |
| سرویس‌ها | `backend/app/services/` |
| پوشش و lock | `backend/app/services/package_service.py` |
| بهینه‌سازی | `backend/app/optimization_engine.py`, `backend/app/optimization_engine_enhanced.py` |
| ورود Frontend | `frontend/src/index.tsx`, `frontend/src/App.tsx` |
| صفحات | `frontend/src/pages/` |
| API کلاینت | `frontend/src/services/api.ts` |
| تست‌ها | `backend/tests/` |
| اسکریپت دمو | `backend/scripts/create_it_procurement_demo_1405.py` |
| Compose | `docker-compose.yml` |

### Routerهای مهم برای باز کردن در جلسه

| ماژول | فایل |
| --- | --- |
| auth / users | `backend/app/routers/auth.py`, `users.py` |
| projects / items | `projects.py`, `items.py`, `items_master.py` |
| procurement | `procurement.py`, `procurement_assignments.py`, `packages.py` |
| decisions / plan | `decisions.py`, `procurement_plan.py` |
| finance | `finance.py`, `invoice_payment_simple.py`, `supplier_payments.py` |
| dashboard / reports | `dashboard.py`, `reports.py`, `analytics.py` |
| audit / config | `audit.py`, `config.py` |

## شاهد مستندات

| موضوع | مسیر |
| --- | --- |
| وضعیت runtime همین بسته | `docs/evaluation/00_current_runtime_and_source_state.md` |
| پشته فناوری | `docs/evaluation/01_technology_stack_fa.md` |
| نقشه کد | `docs/evaluation/02_codebase_map_fa.md` |
| معماری | `docs/evaluation/03_architecture_fa.md` |
| ماتریس قابلیت | `docs/evaluation/04_capability_evidence_matrix_fa.md` |
| راهنمای دمو | `docs/evaluation/05_live_demo_runbook_fa.md` |
| برگه مطالعه | `docs/evaluation/06_technical_cheat_sheet_fa.md` |
| پرسش و پاسخ | `docs/evaluation/07_evaluator_qna_fa.md` |
| داده دمو | `docs/evaluation/08_demo_data_readiness_fa.md` |
| استقرار | `docs/restart-audit/03_run_and_deployment.md` |
| گزارش دیتاست ۱۴۰۵ | `docs/restart-audit/32_it_demo_data_1405_feed_report.md` |
| بسته انتشار | `release_packages/corbit-rivar-rc1/` |
| محدودیت‌های شناخته‌شده | `release_packages/corbit-rivar-rc1/KNOWN_LIMITATIONS.md` |
| یادداشت انتشار | `release_packages/corbit-rivar-rc1/RELEASE_NOTES.md` |

UAT signoff جدا اگر در بسته RC1 موجود بود نشان دهید؛ ادعای امضای رسمی جدید نسازید مگر فایل را همان لحظه باز کنید.

## شاهد فرمان

```bash
# سلامت
curl -sS http://127.0.0.1:8000/health
cd /root/pdss && docker compose ps

# داده دمو — فقط verify
docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_it_procurement_demo_1405.py --mode verify

# تست backend (ممکن است collection روی phase13f بشکند)
docker compose run --rm backend python -m pytest tests -q

# ساخت frontend
docker compose run --rm frontend npm run build
```

روی سرور زنده این فرمان‌ها را از `/root/pdss` اجرا کنید. `.env` را cat نکنید.

## شاهد فرآیند کسب‌وکار

| فرآیند | UI | API / ماژول | داده دمو |
| --- | --- | --- | --- |
| پروژه‌ها | `/projects` | `/projects` | ۳۰ پروژه `DEMO_IT_1405_` |
| اقلام پایه و زیرقلم | `/items-master` | `/items-master` | ۲۶ master / ۱۳۱ sub-item |
| اقلام پروژه | اقلام داخل پروژه | `/items` | ۹۰۰ قلم |
| نهایی‌سازی | Finalize | `PUT /items/{id}/finalize` | ۲۷۰ نهایی |
| تخصیص تأمین | تب Assignments | `/procurement-assignments` | ۲۷۰ تخصیص |
| تأمین‌کنندگان | `/suppliers` | `/suppliers` | ۱۲ تأمین‌کننده |
| پوشش بسته | Coverage modal | `/packages/coverage/{item_id}` | ۶۴۸ بسته / ۳۴۰۱ ردیف |
| تصمیم / بهینه‌سازی | `/optimization-enhanced` | `/finance/optimize-enhanced` | ۲۱۶ آماده؛ lock نشده |
| مالی | `/finance` | `/api/invoice-payment`, `/supplier-payments` | پس از تصمیم |
| گزارش / داشبورد | `/reports`, `/dashboard` | `/reports/`, `/dashboard/*` | بودجه ۷ دوره |
| ممیزی | `/audit-logs` | `GET /audit-logs/` | ورود admin |

## ترتیب پیشنهادی نشان دادن شاهد اگر UI قطع شد

1. `curl /health`
2. `docker compose ps`
3. همان endpoint از OpenAPI
4. فایل router یا سرویس
5. مدل در `models.py`
6. `--mode verify`
7. تست هم‌نام در `backend/tests/`
