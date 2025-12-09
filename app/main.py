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
import uuid

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging, get_logger, log_api_request, log_error
from app.db.session import init_db

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting AI Prompterly Platform API...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"API Prefix: {settings.API_V1_PREFIX}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info("=" * 60)

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)

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

    logger.info("API startup complete - Ready to accept requests")

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
    """Log all requests with timing and generate request ID"""
    # Generate unique request ID
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # Log incoming request
    logger.info(
        f"[{request_id}] --> {request.method} {request.url.path} from {client_ip}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'endpoint': request.url.path,
            'ip_address': client_ip
        }
    )

    start_time = time.time()
    response = None
    error_msg = None

    try:
        response = await call_next(request)
    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"[{request_id}] Unhandled error in middleware: {e}",
            exc_info=True,
            extra={'request_id': request_id}
        )
        raise
    finally:
        # Calculate processing time
        duration_ms = (time.time() - start_time) * 1000
        status_code = response.status_code if response else 500

        # Log the completed request
        log_api_request(
            logger=logger,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
            request_id=request_id,
            ip_address=client_ip,
            error=error_msg
        )

        # Add headers to response
        if response:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

    return response


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Handle custom application exceptions
    Returns structured error response for frontend
    """
    request_id = getattr(request.state, 'request_id', 'unknown')

    logger.warning(
        f"[{request_id}] AppException: {exc.error_code} - {exc.message}",
        extra={
            'request_id': request_id,
            'error_code': exc.error_code,
            'endpoint': request.url.path,
            'method': request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers={"X-Request-ID": request_id}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors
    Returns structured error response with field-level details
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    errors = exc.errors()

    # Extract first error for main message
    first_error = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", ["unknown"])[1:])
    error_type = first_error.get("type", "validation_error")
    error_msg = first_error.get("msg", "Validation failed")

    # Build field errors map
    field_errors = {}
    for error in errors:
        field_path = ".".join(str(loc) for loc in error.get("loc", [])[1:])
        if field_path:
            field_errors[field_path] = error.get("msg", "Invalid value")

    logger.warning(
        f"[{request_id}] ValidationError: {field} - {error_msg}",
        extra={
            'request_id': request_id,
            'error_code': 'VALIDATION_ERROR',
            'endpoint': request.url.path,
            'field_errors': field_errors
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": f"Invalid {field}: {error_msg}" if field else error_msg,
            "details": {
                "field": field,
                "type": error_type,
                "field_errors": field_errors
            }
        },
        headers={"X-Request-ID": request_id}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle all uncaught exceptions
    Returns generic error in production, detailed error in debug mode
    """
    request_id = getattr(request.state, 'request_id', 'unknown')

    log_error(
        logger=logger,
        error=exc,
        context={
            'endpoint': request.url.path,
            'method': request.method
        },
        request_id=request_id
    )

    # In production, don't expose internal error details
    if settings.DEBUG:
        message = f"{type(exc).__name__}: {str(exc)}"
    else:
        message = "An unexpected error occurred. Please try again later."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": message,
            "request_id": request_id
        },
        headers={"X-Request-ID": request_id}
    )


# =============================================================================
# Health & Root Endpoints
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns API status and version
    """
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.APP_ENV
    }


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


# =============================================================================
# API Routers
# =============================================================================

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

logger.info(f"Registered {len(app.routes)} routes")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
