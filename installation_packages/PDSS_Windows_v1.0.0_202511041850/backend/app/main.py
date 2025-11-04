"""
Main FastAPI application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from app.routers import auth, users, projects, items, items_master, procurement, procurement_plan, finance, excel, phases, weights, decisions, dashboard, delivery_options, files, analytics, reports, currencies, invoice_payment_simple, supplier_payments, brs_api, suppliers, audit  # , exchange_rates  # Temporarily disabled due to Pydantic recursion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting up Procurement DSS API...")
    await init_db()
    logger.info("Database initialized successfully")
    
    # Seed sample data
    try:
        from app.seed_data import seed_sample_data
        await seed_sample_data()
        logger.info("Sample data seeded successfully")
    except Exception as e:
        logger.warning(f"Failed to seed sample data: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Procurement DSS API...")


# Create FastAPI application
app = FastAPI(
    title="Procurement DSS API",
    description="Project Procurement & Financial Optimization Decision Support System",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware - ensure it's applied before other middleware
# This ensures CORS headers are included even in error responses
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Global exception handler - ensures CORS headers are always included
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    Ensures CORS headers are included even when exceptions bypass middleware.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Create response with CORS headers
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    
    # Ensure CORS headers are added even for errors
    # CORSMiddleware should handle this, but we ensure it here as fallback
    origin = request.headers.get("origin")
    if origin:
        # Check if origin is allowed (basic check)
        allowed_origins = settings.get_allowed_origins()
        if "*" in allowed_origins or origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(items_master.router)
app.include_router(items.router)
app.include_router(phases.router)
app.include_router(weights.router)
app.include_router(decisions.router)
app.include_router(delivery_options.router)
app.include_router(procurement.router)
app.include_router(procurement_plan.router)
app.include_router(finance.router)
app.include_router(excel.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(files.router)
app.include_router(currencies.router)
app.include_router(brs_api.router)
app.include_router(suppliers.router)
app.include_router(invoice_payment_simple.router)
app.include_router(supplier_payments.router)
# app.include_router(exchange_rates.router)  # Temporarily disabled due to Pydantic recursion
app.include_router(audit.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Procurement DSS API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
