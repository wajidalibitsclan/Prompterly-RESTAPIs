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
    Payment,
    BillingInterval,
    SubscriptionStatus,
    PaymentProvider,
    PaymentStatus
)
from app.db.models.misc import (
    Notification,
    StaticPage,
    FAQ,
    ComplianceRequest,
    NotificationChannel,
    NotificationStatus,
    RequestType,
    RequestStatus
)
from app.db.models.knowledge_base import (
    KBCategory,
    KBPrompt,
    KBDocument,
    KBDocumentChunk,
    KBFaq
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
    "Payment",
    "BillingInterval",
    "SubscriptionStatus",
    "PaymentProvider",
    "PaymentStatus",
    
    # Misc models
    "Notification",
    "StaticPage",
    "FAQ",
    "ComplianceRequest",
    "NotificationChannel",
    "NotificationStatus",
    "RequestType",
    "RequestStatus",

    # Knowledge Base models
    "KBCategory",
    "KBPrompt",
    "KBDocument",
    "KBDocumentChunk",
    "KBFaq",
]
