"""
Database models package
Exports all models for easy importing
"""
from app.db.models.user import User, UserRole
from app.db.models.auth import OAuthAccount, OAuthProvider, UserSession
from app.db.models.mentor import Mentor, MentorStatus, Category
from app.db.models.lounge import (
    Lounge,
    LoungeMembership,
    AccessType,
    MembershipRole
)
from app.db.models.chat import (
    ChatThread,
    ChatMessage,
    ThreadStatus,
    SenderType
)
from app.db.models.file import File, MessageAttachment
from app.db.models.note import Note, TimeCapsule, CapsuleStatus
from app.db.models.billing import (
    SubscriptionPlan,
    Subscription,
    LoungeSubscription,
    Payment,
    BillingInterval,
    LoungePlanType,
    SubscriptionStatus,
    PaymentProvider,
    PaymentStatus
)
from app.db.models.misc import (
    Notification,
    StaticPage,
    FAQ,
    ComplianceRequest,
    ContactMessage,
    NotificationChannel,
    NotificationStatus,
    RequestType,
    RequestStatus,
    ContactMessageStatus
)
from app.db.models.knowledge_base import (
    KBCategory,
    KBPrompt,
    KBDocument,
    KBDocumentChunk,
    KBFaq
)
from app.db.models.background_job import (
    BackgroundJob,
    JobStatus,
    JobType
)

__all__ = [
    # User models
    "User",
    "UserRole",
    "OAuthAccount",
    "OAuthProvider",
    "UserSession",
    
    # Mentor models
    "Mentor",
    "MentorStatus",
    "Category",
    
    # Lounge models
    "Lounge",
    "LoungeMembership",
    "AccessType",
    "MembershipRole",
    
    # Chat models
    "ChatThread",
    "ChatMessage",
    "ThreadStatus",
    "SenderType",
    
    # File models
    "File",
    "MessageAttachment",
    
    # Note models
    "Note",
    "TimeCapsule",
    "CapsuleStatus",
    
    # Billing models
    "SubscriptionPlan",
    "Subscription",
    "LoungeSubscription",
    "Payment",
    "BillingInterval",
    "LoungePlanType",
    "SubscriptionStatus",
    "PaymentProvider",
    "PaymentStatus",
    
    # Misc models
    "Notification",
    "StaticPage",
    "FAQ",
    "ComplianceRequest",
    "ContactMessage",
    "NotificationChannel",
    "NotificationStatus",
    "RequestType",
    "RequestStatus",
    "ContactMessageStatus",

    # Knowledge Base models
    "KBCategory",
    "KBPrompt",
    "KBDocument",
    "KBDocumentChunk",
    "KBFaq",

    # Background Job models
    "BackgroundJob",
    "JobStatus",
    "JobType",
]
