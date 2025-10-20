-- Test script to verify optimization only uses finalized items

-- Step 1: Show items with 0 finalized options
SELECT 
    'Items with ZERO finalized options (should NOT be optimized):' as check_type;
SELECT pi.item_code, 
       COUNT(po.id) as total_options, 
       SUM(CASE WHEN po.is_finalized THEN 1 ELSE 0 END) as finalized_options
FROM project_items pi 
LEFT JOIN procurement_options po ON pi.item_code = po.item_code AND po.is_active = true
WHERE pi.project_id IN (SELECT id FROM projects WHERE is_active = true)
GROUP BY pi.item_code 
HAVING SUM(CASE WHEN po.is_finalized THEN 1 ELSE 0 END) = 0 OR COUNT(po.id) = 0
ORDER BY pi.item_code;

-- Step 2: Get the latest optimization run ID
SELECT 
    'Latest optimization run:' as info,
    run_id,
    run_timestamp,
    COUNT(*) as items_optimized
FROM optimization_results
WHERE run_timestamp = (SELECT MAX(run_timestamp) FROM optimization_results)
GROUP BY run_id, run_timestamp;

-- Step 3: Check if any items with 0 finalized options appear in latest optimization
SELECT 
    'Items with 0 finalized options that INCORRECTLY appeared in latest optimization:' as error_check;
SELECT DISTINCT orr.item_code, orr.run_timestamp
FROM optimization_results orr
WHERE orr.run_timestamp = (SELECT MAX(run_timestamp) FROM optimization_results)
  AND orr.item_code IN (
    SELECT pi.item_code
    FROM project_items pi 
    LEFT JOIN procurement_options po ON pi.item_code = po.item_code AND po.is_active = true
    WHERE pi.project_id IN (SELECT id FROM projects WHERE is_active = true)
    GROUP BY pi.item_code 
    HAVING SUM(CASE WHEN po.is_finalized THEN 1 ELSE 0 END) = 0 OR COUNT(po.id) = 0
  );

