# AI Coaching Lounges - Complete Implementation Guide

## Current Status: Foundation Complete ✅

### Completed Components (Milestone 1)

#### Core Infrastructure
1. **Configuration** (`app/core/config.py`)
   - Environment variable management
   - Type-safe settings with Pydantic
   - Support for all required services

2. **Security** (`app/core/security.py`)
   - Password hashing (bcrypt)
   - JWT token generation (access & refresh)
   - Email verification tokens
   - Password reset tokens
   - Token decoding and validation

3. **JWT Dependencies** (`app/core/jwt.py`)
   - User authentication dependency
   - Active user check
   - Mentor role guard
   - Admin role guard
   - Optional authentication

#### Database Layer
4. **Session Management** (`app/db/session.py`)
   - SQLAlchemy engine configuration
   - Connection pooling
   - Session factory
   - Dependency injection

5. **Complete Database Models** (16 tables)
   - ✅ User & UserRole
   - ✅ OAuthAccount & OAuthProvider
   - ✅ UserSession
   - ✅ Mentor & MentorStatus
   - ✅ Category
   - ✅ Lounge & AccessType
   - ✅ LoungeMembership & MembershipRole
   - ✅ ChatThread & ThreadStatus
   - ✅ ChatMessage & SenderType
   - ✅ File
   - ✅ MessageAttachment
   - ✅ Note
   - ✅ TimeCapsule & CapsuleStatus
   - ✅ SubscriptionPlan & BillingInterval
   - ✅ Subscription & SubscriptionStatus
   - ✅ Payment & PaymentProvider & PaymentStatus
   - ✅ Notification & NotificationChannel & NotificationStatus
   - ✅ StaticPage
   - ✅ FAQ
   - ✅ ComplianceRequest & RequestType & RequestStatus

6. **Main Application** (`app/main.py`)
   - FastAPI initialization
   - Lifespan management
   - CORS middleware
   - GZip compression
   - Request logging
   - Exception handling
   - Health check endpoint

7. **Schemas** (`app/schemas/`)
   - Authentication schemas
   - User schemas
   - Token schemas

## Implementation Plan

### Milestone 2: Authentication API (1-2 days)
**Priority: CRITICAL**

Create `app/api/v1/auth.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core import security
from app.db.models.user import User
from app.schemas.auth import *

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(...)

@router.post("/login", response_model=Token)
async def login(...)

@router.post("/refresh", response_model=Token)
async def refresh_token(...)

@router.post("/logout")
async def logout(...)

@router.post("/verify-email")
async def verify_email(...)

@router.post("/forgot-password")
async def forgot_password(...)

@router.post("/reset-password")
async def reset_password(...)

@router.get("/google")
async def google_login(...)

@router.get("/google/callback")
async def google_callback(...)
```

**Testing Checklist:**
- [ ] User can register
- [ ] User can login
- [ ] JWT tokens work
- [ ] Email verification works
- [ ] Password reset works
- [ ] Google OAuth works
- [ ] Token refresh works
- [ ] Logout works

### Milestone 3: User Management API (1 day)

Create `app/api/v1/users.py`:
```python
@router.get("/me", response_model=UserResponse)
@router.put("/me", response_model=UserResponse)
@router.patch("/me/password")
@router.get("/me/activity")
@router.delete("/me")
```

### Milestone 4: Mentor System (1-2 days)

Create schemas and endpoints:
```python
# app/schemas/mentor.py
class MentorCreate(BaseModel)
class MentorResponse(BaseModel)
class MentorUpdate(BaseModel)

# app/api/v1/mentors.py
@router.get("/")  # List all mentors
@router.get("/{id}")  # Get mentor details
@router.post("/apply")  # Apply to become mentor
@router.get("/{id}/lounges")  # Get mentor lounges
```

### Milestone 5: Lounge System (2 days)

Create schemas and endpoints:
```python
# app/schemas/lounge.py
class LoungeCreate(BaseModel)
class LoungeResponse(BaseModel)
class LoungeUpdate(BaseModel)
class LoungeMemberResponse(BaseModel)

# app/api/v1/lounges.py
@router.get("/")  # List lounges
@router.post("/")  # Create lounge (mentor only)
@router.get("/{id}")  # Get lounge details
@router.put("/{id}")  # Update lounge (mentor only)
@router.delete("/{id}")  # Delete lounge (mentor only)
@router.post("/{id}/join")  # Join lounge
@router.post("/{id}/leave")  # Leave lounge
@router.get("/{id}/members")  # Get lounge members
```

### Milestone 6: AI Chat System (3-4 days)
**Priority: HIGH**

Step 1: Create AI Service
```python
# app/services/ai_service.py
class AIService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def generate_response(
        self,
        messages: List[dict],
        context: Optional[str] = None,
        use_anthropic: bool = False
    ) -> str:
        """Generate AI response"""
        pass
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create text embedding for RAG"""
        pass
    
    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[dict]:
        """Search similar content using vector similarity"""
        pass
```

Step 2: Create Chat Service
```python
# app/services/chat_service.py
class ChatService:
    def __init__(self, db: Session, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
    
    async def create_thread(
        self,
        user_id: int,
        lounge_id: Optional[int] = None
    ) -> ChatThread:
        """Create new chat thread"""
        pass
    
    async def send_message(
        self,
        thread_id: int,
        user_id: int,
        content: str,
        attachments: List[int] = []
    ) -> ChatMessage:
        """Send message and get AI response"""
        pass
    
    async def get_rag_context(
        self,
        user_id: int,
        query: str
    ) -> str:
        """Get RAG context from user notes"""
        pass
```

Step 3: Create Endpoints
```python
# app/api/v1/chat.py
@router.get("/threads")
@router.post("/threads")
@router.get("/threads/{id}")
@router.delete("/threads/{id}")
@router.post("/threads/{id}/messages")
@router.get("/threads/{id}/messages")
@router.post("/upload")
```

### Milestone 7: File Management (1-2 days)

```python
# app/services/file_service.py
class FileService:
    def __init__(self):
        self.s3_client = boto3.client('s3')
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: int
    ) -> File:
        """Upload file to S3 and save metadata"""
        pass
    
    async def get_presigned_url(
        self,
        file_id: int,
        expiration: int = 3600
    ) -> str:
        """Generate presigned URL for file download"""
        pass
    
    async def delete_file(self, file_id: int):
        """Delete file from S3 and database"""
        pass
```

### Milestone 8: Notes System (1 day)

```python
# app/api/v1/notes.py
@router.get("/")  # List notes
@router.post("/")  # Create note
@router.get("/{id}")  # Get note
@router.put("/{id}")  # Update note
@router.delete("/{id}")  # Delete note
@router.patch("/{id}/pin")  # Pin/unpin note
@router.post("/search")  # Search notes
```

### Milestone 9: Time Capsules (1 day)

```python
# app/api/v1/capsules.py
@router.get("/")  # List capsules
@router.post("/")  # Create capsule
@router.get("/{id}")  # Get capsule
@router.post("/{id}/unlock")  # Unlock capsule
```

### Milestone 10: Billing System (2-3 days)

```python
# app/services/billing_service.py
class BillingService:
    def __init__(self):
        self.stripe = stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    async def create_checkout_session(
        self,
        user_id: int,
        plan_id: int
    ) -> str:
        """Create Stripe checkout session"""
        pass
    
    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ):
        """Handle Stripe webhook events"""
        pass
    
    async def cancel_subscription(
        self,
        subscription_id: int
    ):
        """Cancel user subscription"""
        pass

# app/api/v1/billing.py
@router.get("/plans")
@router.post("/checkout")
@router.get("/subscription")
@router.post("/subscription/cancel")
@router.post("/webhook")
@router.get("/invoices")
```

### Milestone 11: Notifications (1 day)

```python
# app/api/v1/notifications.py
@router.get("/")
@router.patch("/{id}/read")
@router.patch("/read-all")
```

### Milestone 12: CMS (1 day)

```python
# app/api/v1/cms.py
@router.get("/pages/{slug}")
@router.get("/faqs")
```

### Milestone 13: Admin Dashboard (2 days)

```python
# app/api/v1/admin.py
@router.get("/stats")
@router.get("/users")
@router.patch("/users/{id}/role")
@router.get("/mentors/pending")
@router.patch("/mentors/{id}/approve")
@router.patch("/mentors/{id}/reject")
@router.put("/cms/pages/{id}")
@router.put("/faqs/{id}")
```

### Milestone 14: Background Workers (2 days)

```python
# app/workers/celery_app.py
from celery import Celery

celery_app = Celery(
    "ai_coaching_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# app/workers/tasks.py
@celery_app.task
def send_email(to: str, subject: str, body: str):
    """Send email via SMTP"""
    pass

@celery_app.task
def unlock_capsules():
    """Check and unlock time capsules"""
    pass

@celery_app.task
def generate_embeddings(note_id: int):
    """Generate embeddings for note"""
    pass

@celery_app.task
def process_stripe_webhook(event_data: dict):
    """Process Stripe webhook asynchronously"""
    pass
```

### Milestone 15: Testing (2-3 days)

```python
# tests/test_auth.py
def test_user_registration()
def test_user_login()
def test_token_refresh()
def test_email_verification()
def test_password_reset()

# tests/test_mentors.py
def test_mentor_application()
def test_mentor_approval()
def test_mentor_listing()

# tests/test_lounges.py
def test_lounge_creation()
def test_lounge_membership()
def test_lounge_listing()

# tests/test_chat.py
def test_thread_creation()
def test_message_sending()
def test_ai_response()

# tests/test_billing.py
def test_checkout_creation()
def test_subscription_activation()
def test_webhook_handling()
```

### Milestone 16: Deployment (1-2 days)

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis
  
  mysql:
    image: mysql:8
    environment:
      MYSQL_DATABASE: ai_coaching
      MYSQL_ROOT_PASSWORD: password
  
  redis:
    image: redis:alpine
  
  celery:
    build: .
    command: celery -A app.workers.celery_app worker --loglevel=info
    depends_on:
      - redis
```

## Development Workflow

### 1. Setup Development Environment
```bash
# Clone repository
git clone [repo-url]
cd ai-coaching-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration
```

### 2. Initialize Database
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE ai_coaching;"

# Initialize Alembic
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 3. Run Development Server
```bash
# Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker (in separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Run tests
pytest tests/ -v --cov=app
```

## Estimated Timeline

Total: **20-30 days** for complete implementation

- Milestone 2 (Auth): 1-2 days ✓
- Milestone 3 (Users): 1 day ✓
- Milestone 4 (Mentors): 1-2 days
- Milestone 5 (Lounges): 2 days
- Milestone 6 (AI Chat): 3-4 days
- Milestone 7 (Files): 1-2 days
- Milestone 8 (Notes): 1 day
- Milestone 9 (Capsules): 1 day
- Milestone 10 (Billing): 2-3 days
- Milestone 11 (Notifications): 1 day
- Milestone 12 (CMS): 1 day
- Milestone 13 (Admin): 2 days
- Milestone 14 (Workers): 2 days
- Milestone 15 (Testing): 2-3 days
- Milestone 16 (Deployment): 1-2 days

## Next Immediate Steps

1. **Create router __init__ files**
2. **Implement auth.py (Milestone 2)**
3. **Implement users.py (Milestone 3)**
4. **Test authentication flow**
5. **Create email service**
6. **Continue with remaining milestones**

Would you like me to implement Milestone 2 (Authentication API) next?
