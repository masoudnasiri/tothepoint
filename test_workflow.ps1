# Complete Platform Workflow Test
# Uses actual API endpoints that the frontend uses

$BASE_URL = "http://localhost:8000"

Write-Host "`n=== STEP 1: Login as Admin ===" -ForegroundColor Cyan
$loginBody = @{ username = "admin"; password = "admin123" } | ConvertTo-Json
$loginResponse = Invoke-RestMethod -Uri "$BASE_URL/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
$adminToken = $loginResponse.access_token
$headers = @{ "Authorization" = "Bearer $adminToken"; "Content-Type" = "application/json" }
Write-Host "✓ Logged in as admin" -ForegroundColor Green

Write-Host "`n=== STEP 2: Get Project Items ===" -ForegroundColor Cyan
$items = Invoke-RestMethod -Uri "$BASE_URL/items/project/1" -Method GET -Headers $headers
Write-Host "✓ Found $($items.items.Count) items in project 1" -ForegroundColor Green

# Take first 3 items for testing
$testItems = $items.items | Select-Object -First 3

Write-Host "`n=== STEP 3: Add Delivery Options ===" -ForegroundColor Cyan
foreach ($item in $testItems) {
    Write-Host "Adding delivery options for $($item.item_code)..." -ForegroundColor Gray
    
    # Add 3 delivery options
    $dates = @("2025-03-01", "2025-03-15", "2025-04-01")
    $slots = @("Morning", "Afternoon", "Evening")
    
    for ($i = 0; $i -lt 3; $i++) {
        $deliveryBody = @{
            item_code = $item.item_code
            delivery_date = $dates[$i]
            delivery_slot = $slots[$i]
            capacity = 100
            cost = 50.0
        } | ConvertTo-Json
        
        try {
            Invoke-RestMethod -Uri "$BASE_URL/delivery/options" -Method POST -Body $deliveryBody -Headers $headers | Out-Null
            Write-Host "  ✓ Added delivery option: $($dates[$i]) $($slots[$i])" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ Failed: $_" -ForegroundColor Red
        }
    }
}

Write-Host "`n=== STEP 4: Finalize Items ===" -ForegroundColor Cyan
foreach ($item in $testItems) {
    Write-Host "Finalizing $($item.item_code)..." -ForegroundColor Gray
    $finalizeBody = @{ is_finalized = $true } | ConvertTo-Json
    
    try {
        Invoke-RestMethod -Uri "$BASE_URL/items/$($item.id)/finalize" -Method PUT -Body $finalizeBody -Headers $headers | Out-Null
        Write-Host "  ✓ Item finalized" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Failed: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== STEP 5: Login as Procurement ===" -ForegroundColor Cyan
$procLoginBody = @{ username = "procurement1"; password = "proc123" } | ConvertTo-Json
$procLoginResponse = Invoke-RestMethod -Uri "$BASE_URL/auth/login" -Method POST -Body $procLoginBody -ContentType "application/json"
$procToken = $procLoginResponse.access_token
$procHeaders = @{ "Authorization" = "Bearer $procToken"; "Content-Type" = "application/json" }
Write-Host "✓ Logged in as procurement1" -ForegroundColor Green

Write-Host "`n=== STEP 6: View Finalized Items ===" -ForegroundColor Cyan
$finalizedItems = Invoke-RestMethod -Uri "$BASE_URL/items/finalized" -Method GET -Headers $procHeaders
Write-Host "✓ Found $($finalizedItems.Count) finalized items" -ForegroundColor Green

Write-Host "`n=== STEP 7: Add Procurement Options ===" -ForegroundColor Cyan
$suppliers = @(
    @{ name = "Dell Direct"; cost = 5000 },
    @{ name = "Vendor A"; cost = 4800 },
    @{ name = "Vendor B"; cost = 5200 }
)

$optionIds = @{}
foreach ($item in $testItems) {
    Write-Host "Adding procurement options for $($item.item_code)..." -ForegroundColor Gray
    $itemOptionIds = @()
    
    foreach ($supplier in $suppliers) {
        $procBody = @{
            item_code = $item.item_code
            supplier_name = $supplier.name
            base_cost = $supplier.cost
            currency_id = 1
            shipping_cost = 100.0
            lomc_lead_time = 30
            payment_terms = @{ type = "cash"; discount_percent = 0 }
        } | ConvertTo-Json
        
        try {
            $response = Invoke-RestMethod -Uri "$BASE_URL/procurement/options" -Method POST -Body $procBody -Headers $procHeaders
            $itemOptionIds += $response.id
            Write-Host "  ✓ Added option from $($supplier.name) - Cost: $($supplier.cost)" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ Failed: $_" -ForegroundColor Red
        }
    }
    
    $optionIds[$item.item_code] = $itemOptionIds
}

Write-Host "`n=== STEP 8: Finalize Best Procurement Option ===" -ForegroundColor Cyan
foreach ($item in $testItems) {
    Write-Host "Finalizing best option for $($item.item_code)..." -ForegroundColor Gray
    $ids = $optionIds[$item.item_code]
    
    if ($ids -and $ids.Count -gt 1) {
        # Finalize second option (Vendor A with best price 4800)
        $bestId = $ids[1]
        $finalizeBody = @{ is_finalized = $true } | ConvertTo-Json
        
        try {
            Invoke-RestMethod -Uri "$BASE_URL/procurement/option/$bestId" -Method PUT -Body $finalizeBody -Headers $procHeaders | Out-Null
            Write-Host "  ✓ Finalized option ID: $bestId (Vendor A @ 4800)" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ Failed: $_" -ForegroundColor Red
        }
    }
}

Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓ Workflow Test Complete!            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "  • Tested $($testItems.Count) items" -ForegroundColor White
Write-Host "  • Added 3 delivery options per item" -ForegroundColor White
Write-Host "  • Finalized all test items" -ForegroundColor White
Write-Host "  • Added 3 procurement options per item" -ForegroundColor White
Write-Host "  • Finalized best procurement option per item" -ForegroundColor White

Write-Host "`nNow check the UI:" -ForegroundColor Yellow
Write-Host "  1. Login as admin - Projects - DC-MOD-2025" -ForegroundColor Gray
Write-Host "  2. See finalized items (first 3)" -ForegroundColor Gray
Write-Host "  3. Login as procurement1 - Procurement" -ForegroundColor Gray
Write-Host "  4. See finalized items with procurement options" -ForegroundColor Gray
Write-Host "  5. Login as finance1 - Finance" -ForegroundColor Gray
Write-Host "  6. See finalized decisions" -ForegroundColor Gray
Write-Host ""

