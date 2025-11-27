"""
Main FastAPI application entry point
AI Coaching Lounges Platform
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging

from app.core.config import settings
from app.db.session import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting AI Prompterly Platform API...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Initialize Sentry if DSN provided
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.APP_ENV,
                traces_sample_rate=0.1 if settings.APP_ENV == "production" else 1.0,
            )
            logger.info("Sentry initialized successfully")
        except Exception as e:
            logger.warning(f"Sentry initialization failed: {e}")
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Prompterly Platform API...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Next-generation AI-powered coaching ecosystem",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request details
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.3f}s "
        f"with status {response.status_code}"
    )
    
    # Add custom header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error" if not settings.DEBUG else str(exc)
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns API status and version
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.APP_ENV
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    Returns welcome message and API information
    """
    return {
        "message": "Welcome to AI Coaching Lounges API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "health": "/health"
    }


# Import and include API routers
from app.api.v1 import auth, users, mentors, lounges, chat, notes, capsules, billing, notifications, cms, admin

# Include API v1 routers
api_v1_prefix = settings.API_V1_PREFIX

app.include_router(auth.router, prefix=f"{api_v1_prefix}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{api_v1_prefix}/users", tags=["Users"])
app.include_router(mentors.router, prefix=f"{api_v1_prefix}/mentors", tags=["Mentors"])
app.include_router(lounges.router, prefix=f"{api_v1_prefix}/lounges", tags=["Lounges"])
app.include_router(chat.router, prefix=f"{api_v1_prefix}/chat", tags=["Chat"])
app.include_router(notes.router, prefix=f"{api_v1_prefix}/notes", tags=["Notes"])
app.include_router(capsules.router, prefix=f"{api_v1_prefix}/capsules", tags=["Time Capsules"])
app.include_router(billing.router, prefix=f"{api_v1_prefix}/billing", tags=["Billing"])
app.include_router(notifications.router, prefix=f"{api_v1_prefix}/notifications", tags=["Notifications"])
app.include_router(cms.router, prefix=f"{api_v1_prefix}/cms", tags=["CMS"])
app.include_router(admin.router, prefix=f"{api_v1_prefix}/admin", tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
