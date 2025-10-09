# Procurement DSS - Endpoint Testing Script
# This script tests all critical endpoints to verify the system is working

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Procurement DSS - Endpoint Tests" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test 1: Backend Health Check
Write-Host "[1/5] Testing Backend Health Endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    if ($healthResponse.status -eq "healthy") {
        Write-Host "  ✅ SUCCESS - Backend is healthy" -ForegroundColor Green
        Write-Host "     Status: $($healthResponse.status)" -ForegroundColor Gray
        Write-Host "     Version: $($healthResponse.version)" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ FAILED - Backend returned unexpected status" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ FAILED - Cannot connect to backend" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: Login Endpoint (Admin)
Write-Host "[2/5] Testing Login Endpoint (Admin)..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method POST -ContentType "application/json" -Body $loginBody
    
    if ($loginResponse.access_token) {
        Write-Host "  ✅ SUCCESS - Login successful" -ForegroundColor Green
        Write-Host "     Token Type: $($loginResponse.token_type)" -ForegroundColor Gray
        Write-Host "     Token: $($loginResponse.access_token.Substring(0, 30))..." -ForegroundColor Gray
        $adminToken = $loginResponse.access_token
    } else {
        Write-Host "  ❌ FAILED - No access token received" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ FAILED - Login request failed" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Get Current User Info
Write-Host "[3/5] Testing Auth/Me Endpoint..." -ForegroundColor Yellow
if ($adminToken) {
    try {
        $headers = @{
            Authorization = "Bearer $adminToken"
        }
        $meResponse = Invoke-RestMethod -Uri "http://localhost:8000/auth/me" -Method GET -Headers $headers
        
        Write-Host "  ✅ SUCCESS - User info retrieved" -ForegroundColor Green
        Write-Host "     Username: $($meResponse.username)" -ForegroundColor Gray
        Write-Host "     Full Name: $($meResponse.full_name)" -ForegroundColor Gray
        Write-Host "     Role: $($meResponse.role)" -ForegroundColor Gray
    } catch {
        Write-Host "  ❌ FAILED - Cannot retrieve user info" -ForegroundColor Red
        Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "  ⏭️  SKIPPED - No token available from login test" -ForegroundColor Yellow
}

Write-Host ""

# Test 4: Frontend Accessibility
Write-Host "[4/5] Testing Frontend Accessibility..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "  ✅ SUCCESS - Frontend is accessible" -ForegroundColor Green
        Write-Host "     Status Code: $($frontendResponse.StatusCode)" -ForegroundColor Gray
        Write-Host "     URL: http://localhost:3000" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ FAILED - Frontend returned unexpected status" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ FAILED - Cannot connect to frontend" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 5: API Documentation
Write-Host "[5/5] Testing API Documentation..." -ForegroundColor Yellow
try {
    $docsResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing
    if ($docsResponse.StatusCode -eq 200) {
        Write-Host "  ✅ SUCCESS - API docs are accessible" -ForegroundColor Green
        Write-Host "     URL: http://localhost:8000/docs" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ FAILED - API docs returned unexpected status" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ FAILED - Cannot access API docs" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor White
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor Gray
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Gray
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Default Credentials:" -ForegroundColor White
Write-Host "  Admin:       admin / admin123" -ForegroundColor Gray
Write-Host "  PM:          pm1 / pm123" -ForegroundColor Gray
Write-Host "  Procurement: proc1 / proc123" -ForegroundColor Gray
Write-Host "  Finance:     finance1 / finance123" -ForegroundColor Gray
Write-Host ""
Write-Host "✨ Testing complete! Open http://localhost:3000 to use the application." -ForegroundColor Green
Write-Host ""
