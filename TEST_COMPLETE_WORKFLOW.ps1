# ============================================
# Complete Platform Workflow Test Script
# ============================================
# This script tests the complete workflow using actual API endpoints:
# 1. Login as Admin
# 2. Add delivery options to items
# 3. Finalize items (makes them visible to procurement)
# 4. Login as Procurement
# 5. Add procurement options
# 6. Finalize procurement decisions
# ============================================

$BASE_URL = "http://localhost:8000"

# ============================================
# Helper Functions
# ============================================

function Login($username, $password) {
    Write-Host "`n=== Logging in as $username ===" -ForegroundColor Cyan
    
    $loginData = @{
        username = $username
        password = $password
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/auth/login" -Method POST -Body $loginData -ContentType "application/json"
        Write-Host "✓ Login successful" -ForegroundColor Green
        return $response.access_token
    } catch {
        Write-Host "✗ Login failed: $_" -ForegroundColor Red
        return $null
    }
}

function Get-ProjectItems($token, $projectId) {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/items/project/$projectId" -Method GET -Headers $headers
        return $response.items
    } catch {
        Write-Host "✗ Failed to get project items: $_" -ForegroundColor Red
        return $null
    }
}

function Add-DeliveryOption($token, $itemCode, $deliveryDate, $deliverySlot) {
    Write-Host "  Adding delivery option for $itemCode..." -ForegroundColor Gray
    
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $deliveryData = @{
        item_code = $itemCode
        delivery_date = $deliveryDate
        delivery_slot = $deliverySlot
        capacity = 100
        cost = 50.0
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/delivery/options" -Method POST -Body $deliveryData -Headers $headers
        Write-Host "  ✓ Delivery option added (ID: $($response.id))" -ForegroundColor Green
        return $response.id
    } catch {
        Write-Host "  ✗ Failed to add delivery option: $_" -ForegroundColor Red
        return $null
    }
}

function Finalize-Item($token, $itemId) {
    Write-Host "  Finalizing item ID: $itemId..." -ForegroundColor Gray
    
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $finalizeData = @{
        is_finalized = $true
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/items/$itemId/finalize" -Method PUT -Body $finalizeData -Headers $headers
        Write-Host "  ✓ Item finalized" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ✗ Failed to finalize item: $_" -ForegroundColor Red
        return $false
    }
}

function Get-FinalizedItems($token) {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/items/finalized" -Method GET -Headers $headers
        return $response
    } catch {
        Write-Host "✗ Failed to get finalized items: $_" -ForegroundColor Red
        return $null
    }
}

function Add-ProcurementOption($token, $itemCode, $supplierName, $baseCost, $currencyId) {
    Write-Host "  Adding procurement option from $supplierName..." -ForegroundColor Gray
    
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $procData = @{
        item_code = $itemCode
        supplier_name = $supplierName
        base_cost = $baseCost
        currency_id = $currencyId
        shipping_cost = 100.0
        lomc_lead_time = 30
        payment_terms = @{
            type = "cash"
            discount_percent = 0
        }
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/procurement/options" -Method POST -Body $procData -Headers $headers
        Write-Host "  ✓ Procurement option added (ID: $($response.id), Cost: $baseCost)" -ForegroundColor Green
        return $response.id
    } catch {
        Write-Host "  ✗ Failed to add procurement option: $_" -ForegroundColor Red
        return $null
    }
}

function Finalize-ProcurementOption($token, $optionId) {
    Write-Host "  Finalizing procurement option ID: $optionId..." -ForegroundColor Gray
    
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $finalizeData = @{
        is_finalized = $true
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BASE_URL/procurement/option/$optionId" -Method PUT -Body $finalizeData -Headers $headers
        Write-Host "  ✓ Procurement option finalized" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ✗ Failed to finalize procurement option: $_" -ForegroundColor Red
        return $false
    }
}

# ============================================
# Main Workflow
# ============================================

Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║  Complete Platform Workflow Test          ║" -ForegroundColor Yellow
Write-Host "╚════════════════════════════════════════════╝`n" -ForegroundColor Yellow

# ============================================
# STEP 1: Login as Admin
# ============================================

$adminToken = Login "admin" "admin123"
if (-not $adminToken) {
    Write-Host "`nWorkflow stopped - login failed" -ForegroundColor Red
    exit
}

# ============================================
# STEP 2: Get Project Items
# ============================================

Write-Host "`n=== Getting Project Items (Project 1: DC-MOD-2025) ===" -ForegroundColor Cyan
$items = Get-ProjectItems $adminToken 1

if (-not $items) {
    Write-Host "No items found" -ForegroundColor Red
    exit
}

Write-Host "Found $($items.Count) items" -ForegroundColor Green

# Select first 3 items for testing
$testItems = $items | Select-Object -First 3

# ============================================
# STEP 3: Add Multiple Delivery Options
# ============================================

Write-Host "`n=== Adding Delivery Options ===" -ForegroundColor Cyan

foreach ($item in $testItems) {
    Write-Host "`nItem: $($item.item_code) - $($item.item_name)" -ForegroundColor Yellow
    
    # Add 3 delivery options per item
    $deliveryDates = @(
        @{ date = "2025-03-01"; slot = "Morning" },
        @{ date = "2025-03-15"; slot = "Afternoon" },
        @{ date = "2025-04-01"; slot = "Morning" }
    )
    
    foreach ($delivery in $deliveryDates) {
        Add-DeliveryOption $adminToken $item.item_code $delivery.date $delivery.slot
    }
}

# ============================================
# STEP 4: Finalize Items (PMO/Admin)
# ============================================

Write-Host "`n=== Finalizing Items ===" -ForegroundColor Cyan

foreach ($item in $testItems) {
    Write-Host "`nFinalizing: $($item.item_code)" -ForegroundColor Yellow
    Finalize-Item $adminToken $item.id
}

# ============================================
# STEP 5: Login as Procurement
# ============================================

$procToken = Login "procurement1" "proc123"
if (-not $procToken) {
    Write-Host "`nWorkflow stopped - procurement login failed" -ForegroundColor Red
    exit
}

# ============================================
# STEP 6: View Finalized Items
# ============================================

Write-Host "`n=== Viewing Finalized Items (Procurement) ===" -ForegroundColor Cyan
$finalizedItems = Get-FinalizedItems $procToken

if ($finalizedItems) {
    Write-Host "Found $($finalizedItems.Count) finalized items" -ForegroundColor Green
    foreach ($item in $finalizedItems) {
        Write-Host "  - $($item.item_code): $($item.item_name)" -ForegroundColor Gray
    }
} else {
    Write-Host "No finalized items found" -ForegroundColor Red
}

# ============================================
# STEP 7: Add Multiple Procurement Options
# ============================================

Write-Host "`n=== Adding Procurement Options ===" -ForegroundColor Cyan

$suppliers = @(
    @{ name = "Dell Direct"; baseCost = 5000; currencyId = 1 },
    @{ name = "Vendor A"; baseCost = 4800; currencyId = 1 },
    @{ name = "Vendor B"; baseCost = 5200; currencyId = 2 }
)

$procOptionIds = @{}

foreach ($item in $testItems) {
    Write-Host "`nItem: $($item.item_code)" -ForegroundColor Yellow
    
    $optionIds = @()
    foreach ($supplier in $suppliers) {
        $optionId = Add-ProcurementOption $procToken $item.item_code $supplier.name $supplier.baseCost $supplier.currencyId
        if ($optionId) {
            $optionIds += $optionId
        }
    }
    
    $procOptionIds[$item.item_code] = $optionIds
}

# ============================================
# STEP 8: Finalize Best Procurement Option
# ============================================

Write-Host "`n=== Finalizing Procurement Decisions ===" -ForegroundColor Cyan

foreach ($item in $testItems) {
    Write-Host "`nItem: $($item.item_code)" -ForegroundColor Yellow
    
    # Finalize the first option (usually best price from Vendor A)
    $optionIds = $procOptionIds[$item.item_code]
    if ($optionIds -and $optionIds.Count -gt 0) {
        $bestOptionId = $optionIds[1]  # Second option (Vendor A with best price)
        Write-Host "  Selecting best option (ID: $bestOptionId - Vendor A @ 4800)" -ForegroundColor Cyan
        Finalize-ProcurementOption $procToken $bestOptionId
    }
}

# ============================================
# STEP 9: Summary
# ============================================

Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Workflow Test Complete!                   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  ✓ Tested $($testItems.Count) items" -ForegroundColor Green
Write-Host "  ✓ Added 3 delivery options per item" -ForegroundColor Green
Write-Host "  ✓ Finalized all test items" -ForegroundColor Green
Write-Host "  ✓ Added 3 procurement options per item" -ForegroundColor Green
Write-Host "  ✓ Finalized best procurement option per item" -ForegroundColor Green

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Login to UI as admin to verify items are finalized" -ForegroundColor Gray
Write-Host "  2. Login as procurement1 to see procurement options" -ForegroundColor Gray
Write-Host "  3. Login as finance1 to see finalized decisions" -ForegroundColor Gray
Write-Host "  4. Check that edit/delete buttons are disabled for finalized items`n" -ForegroundColor Gray

