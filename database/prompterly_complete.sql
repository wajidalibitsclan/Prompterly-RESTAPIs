-- ============================================================
-- Prompterly Platform - Complete Database Schema
-- Generated: 2025-12-31
-- MySQL 8.0+ Compatible
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';

-- ============================================================
-- DROP EXISTING TABLES
-- ============================================================

DROP TABLE IF EXISTS kb_document_chunks;
DROP TABLE IF EXISTS kb_faqs;
DROP TABLE IF EXISTS kb_documents;
DROP TABLE IF EXISTS kb_prompts;
DROP TABLE IF EXISTS kb_categories;
DROP TABLE IF EXISTS message_attachments;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS chat_threads;
DROP TABLE IF EXISTS lounge_subscriptions;
DROP TABLE IF EXISTS lounge_memberships;
DROP TABLE IF EXISTS lounges;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS subscription_plans;
DROP TABLE IF EXISTS time_capsules;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS compliance_requests;
DROP TABLE IF EXISTS faqs;
DROP TABLE IF EXISTS static_pages;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS system_settings;
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS mentors;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS email_otps;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS oauth_accounts;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS alembic_version;

-- ============================================================
-- CORE TABLES
-- ============================================================

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500) DEFAULT NULL,
    role ENUM('member', 'mentor', 'admin') NOT NULL DEFAULT 'member',
    email_verified_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY ix_users_email (email),
    KEY ix_users_id (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE oauth_accounts (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    provider ENUM('google') NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT DEFAULT NULL,
    refresh_token TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_oauth_accounts_id (id),
    KEY fk_oauth_user (user_id),
    CONSTRAINT fk_oauth_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE user_sessions (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    user_agent VARCHAR(500) DEFAULT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    KEY ix_user_sessions_id (id),
    KEY fk_session_user (user_id),
    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE email_otps (
    id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    purpose VARCHAR(50) NOT NULL DEFAULT 'registration',
    expires_at DATETIME NOT NULL,
    verified_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_email_otps_id (id),
    KEY ix_email_otps_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE categories (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY ix_categories_slug (slug),
    KEY ix_categories_id (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE mentors (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    headline VARCHAR(255) DEFAULT NULL,
    bio TEXT DEFAULT NULL,
    intro_video_url VARCHAR(500) DEFAULT NULL,
    experience_years INT DEFAULT 0,
    status ENUM('pending', 'approved', 'disabled') NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_mentors_user_id (user_id),
    KEY ix_mentors_id (id),
    CONSTRAINT fk_mentor_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE files (
    id INT NOT NULL AUTO_INCREMENT,
    owner_user_id INT NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_files_id (id),
    KEY fk_file_owner (owner_user_id),
    CONSTRAINT fk_file_owner FOREIGN KEY (owner_user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- SUBSCRIPTION & BILLING TABLES
-- ============================================================

CREATE TABLE subscription_plans (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    price_cents INT NOT NULL,
    billing_interval ENUM('monthly', 'yearly') NOT NULL,
    features JSON DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    UNIQUE KEY ix_subscription_plans_slug (slug),
    KEY ix_subscription_plans_id (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE subscriptions (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    plan_id INT NOT NULL,
    stripe_subscription_id VARCHAR(255) NOT NULL,
    status ENUM('trialing', 'active', 'past_due', 'canceled') NOT NULL DEFAULT 'trialing',
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    renews_at DATETIME NOT NULL,
    canceled_at DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_subscriptions_stripe_id (stripe_subscription_id),
    KEY ix_subscriptions_id (id),
    KEY fk_subscription_user (user_id),
    KEY fk_subscription_plan (plan_id),
    CONSTRAINT fk_subscription_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_subscription_plan FOREIGN KEY (plan_id) REFERENCES subscription_plans (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE payments (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    provider ENUM('stripe', 'klarna', 'afterpay') NOT NULL,
    provider_payment_id VARCHAR(255) NOT NULL,
    amount_cents INT NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status ENUM('pending', 'succeeded', 'failed') NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_payments_provider_id (provider_payment_id),
    KEY ix_payments_id (id),
    KEY fk_payment_user (user_id),
    CONSTRAINT fk_payment_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- LOUNGE TABLES
-- ============================================================

CREATE TABLE lounges (
    id INT NOT NULL AUTO_INCREMENT,
    mentor_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT DEFAULT NULL,
    category_id INT DEFAULT NULL,
    access_type ENUM('free', 'paid', 'invite_only') NOT NULL DEFAULT 'free',
    plan_id INT DEFAULT NULL,
    max_members INT DEFAULT NULL,
    is_public_listing TINYINT(1) NOT NULL DEFAULT 1,
    profile_image_id INT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    stripe_product_id VARCHAR(255) DEFAULT NULL,
    stripe_monthly_price_id VARCHAR(255) DEFAULT NULL,
    stripe_yearly_price_id VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY ix_lounges_slug (slug),
    KEY ix_lounges_id (id),
    KEY ix_lounges_stripe_product_id (stripe_product_id),
    KEY fk_lounge_mentor (mentor_id),
    KEY fk_lounge_category (category_id),
    KEY fk_lounge_plan (plan_id),
    KEY fk_lounge_profile_image (profile_image_id),
    CONSTRAINT fk_lounge_mentor FOREIGN KEY (mentor_id) REFERENCES mentors (id) ON DELETE CASCADE,
    CONSTRAINT fk_lounge_category FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL,
    CONSTRAINT fk_lounge_plan FOREIGN KEY (plan_id) REFERENCES subscription_plans (id) ON DELETE SET NULL,
    CONSTRAINT fk_lounge_profile_image FOREIGN KEY (profile_image_id) REFERENCES files (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lounge_memberships (
    id INT NOT NULL AUTO_INCREMENT,
    lounge_id INT NOT NULL,
    user_id INT NOT NULL,
    role ENUM('member', 'co_mentor') NOT NULL DEFAULT 'member',
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    left_at DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    KEY ix_lounge_memberships_id (id),
    KEY fk_membership_lounge (lounge_id),
    KEY fk_membership_user (user_id),
    CONSTRAINT fk_membership_lounge FOREIGN KEY (lounge_id) REFERENCES lounges (id) ON DELETE CASCADE,
    CONSTRAINT fk_membership_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lounge_subscriptions (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    lounge_id INT NOT NULL,
    plan_type ENUM('monthly', 'yearly') NOT NULL,
    stripe_subscription_id VARCHAR(255) NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    status ENUM('trialing', 'active', 'past_due', 'canceled') NOT NULL DEFAULT 'active',
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    renews_at DATETIME NOT NULL,
    canceled_at DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_lounge_subscriptions_stripe_id (stripe_subscription_id),
    KEY ix_lounge_subscriptions_id (id),
    KEY ix_lounge_subscriptions_user_id (user_id),
    KEY ix_lounge_subscriptions_lounge_id (lounge_id),
    KEY ix_lounge_subscriptions_user_lounge (user_id, lounge_id),
    CONSTRAINT fk_lounge_subscription_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_lounge_subscription_lounge FOREIGN KEY (lounge_id) REFERENCES lounges (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- CHAT TABLES
-- ============================================================

CREATE TABLE chat_threads (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    lounge_id INT DEFAULT NULL,
    title VARCHAR(255) DEFAULT NULL,
    status ENUM('open', 'archived') NOT NULL DEFAULT 'open',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_chat_threads_id (id),
    KEY fk_thread_user (user_id),
    KEY fk_thread_lounge (lounge_id),
    CONSTRAINT fk_thread_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_thread_lounge FOREIGN KEY (lounge_id) REFERENCES lounges (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE chat_messages (
    id INT NOT NULL AUTO_INCREMENT,
    thread_id INT NOT NULL,
    sender_type ENUM('user', 'ai', 'mentor') NOT NULL,
    user_id INT DEFAULT NULL,
    content TEXT NOT NULL,
    message_metadata JSON DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_chat_messages_id (id),
    KEY fk_message_thread (thread_id),
    KEY fk_message_user (user_id),
    CONSTRAINT fk_message_thread FOREIGN KEY (thread_id) REFERENCES chat_threads (id) ON DELETE CASCADE,
    CONSTRAINT fk_message_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE message_attachments (
    id INT NOT NULL AUTO_INCREMENT,
    message_id INT NOT NULL,
    file_id INT NOT NULL,
    PRIMARY KEY (id),
    KEY ix_message_attachments_id (id),
    KEY fk_attachment_message (message_id),
    KEY fk_attachment_file (file_id),
    CONSTRAINT fk_attachment_message FOREIGN KEY (message_id) REFERENCES chat_messages (id) ON DELETE CASCADE,
    CONSTRAINT fk_attachment_file FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- USER CONTENT TABLES
-- ============================================================

CREATE TABLE notes (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_pinned TINYINT(1) NOT NULL DEFAULT 0,
    is_included_in_rag TINYINT(1) NOT NULL DEFAULT 0,
    tags JSON DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_notes_id (id),
    KEY fk_note_user (user_id),
    CONSTRAINT fk_note_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE time_capsules (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    unlock_at DATETIME NOT NULL,
    status ENUM('locked', 'unlocked', 'expired') NOT NULL DEFAULT 'locked',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_time_capsules_id (id),
    KEY fk_capsule_user (user_id),
    CONSTRAINT fk_capsule_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE notifications (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    type VARCHAR(100) NOT NULL,
    data JSON DEFAULT NULL,
    channel ENUM('email', 'in_app') NOT NULL DEFAULT 'in_app',
    status ENUM('queued', 'sent', 'read') NOT NULL DEFAULT 'queued',
    sent_at DATETIME DEFAULT NULL,
    read_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_notifications_id (id),
    KEY fk_notification_user (user_id),
    CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- KNOWLEDGE BASE TABLES
-- ============================================================

CREATE TABLE kb_categories (
    id INT NOT NULL AUTO_INCREMENT,
    lounge_id INT DEFAULT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT DEFAULT NULL,
    icon VARCHAR(100) DEFAULT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_kb_categories_id (id),
    KEY ix_kb_categories_slug (slug),
    KEY ix_kb_categories_lounge (lounge_id),
    CONSTRAINT fk_kb_category_lounge FOREIGN KEY (lounge_id) REFERENCES lounges (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE kb_prompts (
    id INT NOT NULL AUTO_INCREMENT,
    lounge_id INT DEFAULT NULL,
    category_id INT DEFAULT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    description TEXT DEFAULT NULL,
    tags JSON DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_included_in_rag TINYINT(1) NOT NULL DEFAULT 1,
    usage_count INT NOT NULL DEFAULT 0,
    embedding JSON DEFAULT NULL,
    embedding_model VARCHAR(100) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by_id INT DEFAULT NULL,
    PRIMARY KEY (id),
    KEY ix_kb_prompts_id (id),
    KEY ix_kb_prompts_lounge (lounge_id),
    KEY fk_kb_prompt_category (category_id),
    KEY fk_kb_prompt_creator (created_by_id),
    CONSTRAINT fk_kb_prompt_lounge FOREIGN KEY (lounge_id) REFERENCES lounges (id) ON DELETE CASCADE,
    CONSTRAINT fk_kb_prompt_category FOREIGN KEY (category_id) REFERENCES kb_categories (id) ON DELETE SET NULL,
    CONSTRAINT fk_kb_prompt_creator FOREIGN KEY (created_by_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE kb_documents (
    id INT NOT NULL AUTO_INCREMENT,
    lounge_id INT DEFAULT NULL,
    category_id INT DEFAULT NULL,
    file_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT DEFAULT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    extracted_text TEXT DEFAULT NULL,
    summary TEXT DEFAULT NULL,
    tags JSON DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_processed TINYINT(1) NOT NULL DEFAULT 0,
    processing_error TEXT DEFAULT NULL,
    embedding JSON DEFAULT NULL,
    embedding_model VARCHAR(100) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by_id INT DEFAULT NULL,
    PRIMARY KEY (id),
    KEY ix_kb_documents_id (id),
    KEY ix_kb_documents_lounge (lounge_id),
    KEY fk_kb_document_category (category_id),
    KEY fk_kb_document_file (file_id),
    KEY fk_kb_document_creator (created_by_id),
    CONSTRAINT fk_kb_document_lounge FOREIGN KEY (lounge_id) REFERENCES lounges (id) ON DELETE CASCADE,
    CONSTRAINT fk_kb_document_category FOREIGN KEY (category_id) REFERENCES kb_categories (id) ON DELETE SET NULL,
    CONSTRAINT fk_kb_document_file FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE,
    CONSTRAINT fk_kb_document_creator FOREIGN KEY (created_by_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE kb_document_chunks (
    id INT NOT NULL AUTO_INCREMENT,
    document_id INT NOT NULL,
    content TEXT NOT NULL,
    chunk_index INT NOT NULL,
    start_char INT DEFAULT NULL,
    end_char INT DEFAULT NULL,
    token_count INT DEFAULT NULL,
    embedding JSON DEFAULT NULL,
    embedding_model VARCHAR(100) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_kb_document_chunks_id (id),
    KEY fk_chunk_document (document_id),
    CONSTRAINT fk_chunk_document FOREIGN KEY (document_id) REFERENCES kb_documents (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE kb_faqs (
    id INT NOT NULL AUTO_INCREMENT,
    lounge_id INT DEFAULT NULL,
    category_id INT DEFAULT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    tags JSON DEFAULT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    is_included_in_rag TINYINT(1) NOT NULL DEFAULT 1,
    view_count INT NOT NULL DEFAULT 0,
    helpful_count INT NOT NULL DEFAULT 0,
    not_helpful_count INT NOT NULL DEFAULT 0,
    embedding JSON DEFAULT NULL,
    embedding_model VARCHAR(100) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by_id INT DEFAULT NULL,
    PRIMARY KEY (id),
    KEY ix_kb_faqs_id (id),
    KEY ix_kb_faqs_lounge (lounge_id),
    KEY fk_kb_faq_category (category_id),
    KEY fk_kb_faq_creator (created_by_id),
    CONSTRAINT fk_kb_faq_lounge FOREIGN KEY (lounge_id) REFERENCES lounges (id) ON DELETE CASCADE,
    CONSTRAINT fk_kb_faq_category FOREIGN KEY (category_id) REFERENCES kb_categories (id) ON DELETE SET NULL,
    CONSTRAINT fk_kb_faq_creator FOREIGN KEY (created_by_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- ADMIN & SYSTEM TABLES
-- ============================================================

CREATE TABLE static_pages (
    id INT NOT NULL AUTO_INCREMENT,
    slug VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_published TINYINT(1) NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY ix_static_pages_slug (slug),
    KEY ix_static_pages_id (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE faqs (
    id INT NOT NULL AUTO_INCREMENT,
    category VARCHAR(100) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY ix_faqs_id (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE compliance_requests (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    request_type ENUM('export', 'delete') NOT NULL,
    status ENUM('pending', 'processing', 'done', 'rejected') NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_compliance_requests_id (id),
    KEY fk_compliance_user (user_id),
    CONSTRAINT fk_compliance_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE audit_logs (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT DEFAULT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) DEFAULT NULL,
    entity_id INT DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    user_agent VARCHAR(500) DEFAULT NULL,
    changes JSON DEFAULT NULL,
    metadata JSON DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_audit_logs_id (id),
    KEY ix_audit_logs_action (action),
    KEY fk_audit_user (user_id),
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE system_settings (
    id INT NOT NULL AUTO_INCREMENT,
    `key` VARCHAR(100) NOT NULL,
    value TEXT DEFAULT NULL,
    value_type VARCHAR(20) NOT NULL DEFAULT 'string',
    description TEXT DEFAULT NULL,
    is_public TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY ix_system_settings_key (`key`),
    KEY ix_system_settings_id (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- SEED DATA
-- ============================================================

INSERT INTO alembic_version (version_num) VALUES ('007_add_lounge_subscriptions');

-- Admin User (password: password123)
INSERT INTO users (id, email, password_hash, name, role, email_verified_at, created_at) VALUES
(1, 'admin@prompterly.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Admin', 'admin', NOW(), NOW());

-- Categories
INSERT INTO categories (id, name, slug) VALUES
(1, 'Personal Development', 'personal-development'),
(2, 'Career Growth', 'career-growth'),
(3, 'Health & Wellness', 'health-wellness'),
(4, 'Business', 'business'),
(5, 'Technology', 'technology');

-- System Settings
INSERT INTO system_settings (id, `key`, value, value_type, description, is_public) VALUES
(1, 'maintenance_mode', 'false', 'bool', 'Enable maintenance mode', 0),
(2, 'max_file_size_mb', '10', 'int', 'Maximum file upload size in MB', 1),
(3, 'ai_model_default', 'gpt-4', 'string', 'Default AI model', 0),
(4, 'free_trial_days', '14', 'int', 'Free trial duration', 1),
(5, 'support_email', 'support@prompterly.com', 'string', 'Support email', 1);

-- ============================================================
-- COMPLETION
-- ============================================================

SELECT 'Prompterly database initialized successfully!' AS status;
