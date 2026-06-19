-- ============================================================================
-- SEED FINANCE DATA
-- Creates finalized decisions for Finance page
-- ============================================================================

-- Create finalized decisions (select best option for each item)
-- This simulates that finance team has run optimization and made decisions

WITH finance_user AS (
    SELECT id FROM users WHERE username = 'finance1' LIMIT 1
),
selected_options AS (
    -- Select one "best" option per item (lowest cost in base currency equivalent)
    SELECT DISTINCT ON (po.item_code)
        po.id as procurement_option_id,
        po.item_code,
        po.base_cost,
        po.currency_id,
        po.lomc_lead_time,
        pi.id as project_item_id,
        pi.project_id,
        pi.quantity
    FROM procurement_options po
    JOIN project_items pi ON pi.item_code = po.item_code
    WHERE pi.is_finalized = true
    ORDER BY po.item_code, po.base_cost ASC  -- Select cheapest option
    LIMIT 200  -- Create decisions for first 200 items
)
INSERT INTO finalized_decisions (
    project_id,
    project_item_id,
    item_code,
    procurement_option_id,
    purchase_date,
    delivery_date,
    quantity,
    final_cost,
    final_cost_amount,
    final_cost_currency,
    currency_id,
    status,
    delivery_status,
    decision_maker_id,
    decision_date,
    finalized_at,
    finalized_by_id,
    -- Forecast invoice data
    forecast_invoice_timing_type,
    forecast_invoice_days_after_delivery,
    forecast_invoice_issue_date,
    forecast_invoice_amount,
    forecast_invoice_amount_value,
    forecast_invoice_amount_currency,
    -- Some with actual invoice data (30% of items)
    actual_invoice_issue_date,
    actual_invoice_amount,
    actual_invoice_amount_value,
    actual_invoice_amount_currency,
    actual_invoice_received_date,
    invoice_entered_by_id,
    invoice_entered_at,
    -- Some with payment data (20% of items)
    actual_payment_amount,
    actual_payment_amount_value,
    actual_payment_amount_currency,
    actual_payment_date,
    payment_entered_by_id,
    payment_entered_at
)
SELECT 
    so.project_id,
    so.project_item_id,
    so.item_code,
    so.procurement_option_id,
    CURRENT_DATE + (so.lomc_lead_time - 20 || ' days')::interval AS purchase_date,
    CURRENT_DATE + (so.lomc_lead_time || ' days')::interval AS delivery_date,
    so.quantity,
    so.base_cost * so.quantity AS final_cost,
    so.base_cost * so.quantity AS final_cost_amount,
    (SELECT code FROM currencies WHERE id = so.currency_id),
    so.currency_id,
    CASE 
        WHEN random() < 0.2 THEN 'DELIVERED'
        WHEN random() < 0.5 THEN 'IN_TRANSIT'
        ELSE 'ORDERED'
    END,
    CASE 
        WHEN random() < 0.2 THEN 'DELIVERED'
        WHEN random() < 0.4 THEN 'IN_TRANSIT'
        ELSE 'AWAITING_DELIVERY'
    END,
    fu.id,
    NOW() - (random() * 30 || ' days')::interval,
    NOW() - (random() * 20 || ' days')::interval,
    fu.id,
    -- Forecast invoice
    'DAYS_AFTER_DELIVERY',
    7,
    CURRENT_DATE + (so.lomc_lead_time + 7 || ' days')::interval,
    so.base_cost * so.quantity,
    so.base_cost * so.quantity,
    (SELECT code FROM currencies WHERE id = so.currency_id),
    -- Actual invoice (30% of items have this)
    CASE WHEN random() < 0.3 THEN CURRENT_DATE + (so.lomc_lead_time + (5 + random() * 10)::int || ' days')::interval ELSE NULL END,
    CASE WHEN random() < 0.3 THEN so.base_cost * so.quantity ELSE NULL END,
    CASE WHEN random() < 0.3 THEN so.base_cost * so.quantity ELSE NULL END,
    CASE WHEN random() < 0.3 THEN (SELECT code FROM currencies WHERE id = so.currency_id) ELSE NULL END,
    CASE WHEN random() < 0.3 THEN CURRENT_DATE + (so.lomc_lead_time + (6 + random() * 12)::int || ' days')::interval ELSE NULL END,
    CASE WHEN random() < 0.3 THEN fu.id ELSE NULL END,
    CASE WHEN random() < 0.3 THEN NOW() - (random() * 10 || ' days')::interval ELSE NULL END,
    -- Actual payment (20% of items have this)
    CASE WHEN random() < 0.2 THEN so.base_cost * so.quantity ELSE NULL END,
    CASE WHEN random() < 0.2 THEN so.base_cost * so.quantity ELSE NULL END,
    CASE WHEN random() < 0.2 THEN (SELECT code FROM currencies WHERE id = so.currency_id) ELSE NULL END,
    CASE WHEN random() < 0.2 THEN CURRENT_DATE + (so.lomc_lead_time + (10 + random() * 20)::int || ' days')::interval ELSE NULL END,
    CASE WHEN random() < 0.2 THEN fu.id ELSE NULL END,
    CASE WHEN random() < 0.2 THEN NOW() - (random() * 5 || ' days')::interval ELSE NULL END
FROM selected_options so
CROSS JOIN finance_user fu;

-- Create budget data for Finance page
INSERT INTO budget_data (budget_date, available_budget, multi_currency_budget, created_by_id)
SELECT 
    generate_series(
        CURRENT_DATE - INTERVAL '6 months',
        CURRENT_DATE + INTERVAL '12 months',
        INTERVAL '1 month'
    )::date AS budget_date,
    (500000 + random() * 200000)::numeric(15,2) AS available_budget,
    json_build_object(
        'USD', (300000 + random() * 100000)::numeric(15,2),
        'IRR', (12000000000 + random() * 5000000000)::numeric(15,2),
        'EUR', (250000 + random() * 80000)::numeric(15,2)
    ) AS multi_currency_budget,
    (SELECT id FROM users WHERE username = 'finance1' LIMIT 1)
FROM generate_series(1, 1);  -- Creates monthly budget data

-- Summary
SELECT '========================================' AS "STATUS";
SELECT '✅ FINANCE DATA SEEDED' AS "RESULT";
SELECT '========================================' AS "STATUS";

SELECT 'Table' AS "Component", 'Count' AS "Records"
UNION ALL
SELECT 'Finalized Decisions', COUNT(*)::text FROM finalized_decisions
UNION ALL
SELECT 'Budget Data', COUNT(*)::text FROM budget_data
UNION ALL
SELECT '- With Invoice Data', COUNT(*)::text FROM finalized_decisions WHERE actual_invoice_issue_date IS NOT NULL
UNION ALL
SELECT '- With Payment Data', COUNT(*)::text FROM finalized_decisions WHERE actual_payment_date IS NOT NULL;

SELECT '========================================' AS "STATUS";
SELECT 'Decision Status Breakdown' AS "INFO";
SELECT status, COUNT(*)::text AS count
FROM finalized_decisions
GROUP BY status
ORDER BY status;

SELECT '========================================' AS "STATUS";
SELECT 'Delivery Status Breakdown' AS "INFO";
SELECT delivery_status, COUNT(*)::text AS count
FROM finalized_decisions
GROUP BY delivery_status
ORDER BY delivery_status;

SELECT '========================================' AS "STATUS";
SELECT 'Currency Breakdown (Decisions)' AS "INFO";
SELECT c.code AS currency, COUNT(fd.id)::text AS decisions
FROM currencies c
LEFT JOIN finalized_decisions fd ON fd.currency_id = c.id
GROUP BY c.code
ORDER BY c.code;

SELECT '========================================' AS "STATUS";
SELECT '🚀 Finance page now has data!' AS "NEXT STEP";
SELECT 'Refresh browser and login as finance1' AS "ACTION";


