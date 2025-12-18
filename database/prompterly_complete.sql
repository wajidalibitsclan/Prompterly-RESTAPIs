-- ============================================================
-- Prompterly Platform - Complete Database Schema and Seed Data
-- Generated: 2025-12-18
-- MySQL 8.0+ Compatible
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';

-- ============================================================
-- DROP EXISTING TABLES (in reverse dependency order)
-- ============================================================

DROP TABLE IF EXISTS `kb_document_chunks`;
DROP TABLE IF EXISTS `kb_faqs`;
DROP TABLE IF EXISTS `kb_documents`;
DROP TABLE IF EXISTS `kb_prompts`;
DROP TABLE IF EXISTS `kb_categories`;
DROP TABLE IF EXISTS `message_attachments`;
DROP TABLE IF EXISTS `chat_messages`;
DROP TABLE IF EXISTS `chat_threads`;
DROP TABLE IF EXISTS `lounge_memberships`;
DROP TABLE IF EXISTS `lounges`;
DROP TABLE IF EXISTS `payments`;
DROP TABLE IF EXISTS `subscriptions`;
DROP TABLE IF EXISTS `subscription_plans`;
DROP TABLE IF EXISTS `time_capsules`;
DROP TABLE IF EXISTS `notes`;
DROP TABLE IF EXISTS `notifications`;
DROP TABLE IF EXISTS `compliance_requests`;
DROP TABLE IF EXISTS `faqs`;
DROP TABLE IF EXISTS `static_pages`;
DROP TABLE IF EXISTS `audit_logs`;
DROP TABLE IF EXISTS `system_settings`;
DROP TABLE IF EXISTS `files`;
DROP TABLE IF EXISTS `mentors`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `email_otps`;
DROP TABLE IF EXISTS `user_sessions`;
DROP TABLE IF EXISTS `oauth_accounts`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `alembic_version`;

-- ============================================================
-- CREATE TABLES
-- ============================================================

-- Alembic Version Table
CREATE TABLE `alembic_version` (
    `version_num` VARCHAR(32) NOT NULL,
    PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users Table
CREATE TABLE `users` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `email` VARCHAR(255) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `avatar_url` VARCHAR(500) DEFAULT NULL,
    `role` ENUM('member', 'mentor', 'admin') NOT NULL DEFAULT 'member',
    `email_verified_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_users_email` (`email`),
    KEY `ix_users_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- OAuth Accounts Table
CREATE TABLE `oauth_accounts` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `provider` ENUM('google') NOT NULL,
    `provider_user_id` VARCHAR(255) NOT NULL,
    `access_token` TEXT DEFAULT NULL,
    `refresh_token` TEXT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_oauth_accounts_id` (`id`),
    KEY `fk_oauth_user` (`user_id`),
    CONSTRAINT `fk_oauth_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User Sessions Table
CREATE TABLE `user_sessions` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `ip_address` VARCHAR(45) DEFAULT NULL,
    `user_agent` VARCHAR(500) DEFAULT NULL,
    `expires_at` DATETIME NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `revoked_at` DATETIME DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_user_sessions_id` (`id`),
    KEY `fk_session_user` (`user_id`),
    CONSTRAINT `fk_session_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Email OTPs Table
CREATE TABLE `email_otps` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `email` VARCHAR(255) NOT NULL,
    `otp` VARCHAR(6) NOT NULL,
    `purpose` VARCHAR(50) NOT NULL DEFAULT 'registration',
    `expires_at` DATETIME NOT NULL,
    `verified_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_email_otps_id` (`id`),
    KEY `ix_email_otps_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Categories Table (for lounges)
CREATE TABLE `categories` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_categories_slug` (`slug`),
    KEY `ix_categories_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Mentors Table
CREATE TABLE `mentors` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `headline` VARCHAR(255) DEFAULT NULL,
    `bio` TEXT DEFAULT NULL,
    `intro_video_url` VARCHAR(500) DEFAULT NULL,
    `experience_years` INT DEFAULT 0,
    `status` ENUM('pending', 'approved', 'disabled') NOT NULL DEFAULT 'pending',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_mentors_user_id` (`user_id`),
    KEY `ix_mentors_id` (`id`),
    CONSTRAINT `fk_mentor_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Files Table
CREATE TABLE `files` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `owner_user_id` INT NOT NULL,
    `storage_path` VARCHAR(500) NOT NULL,
    `mime_type` VARCHAR(100) NOT NULL,
    `size_bytes` BIGINT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_files_id` (`id`),
    KEY `fk_file_owner` (`owner_user_id`),
    CONSTRAINT `fk_file_owner` FOREIGN KEY (`owner_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Subscription Plans Table
CREATE TABLE `subscription_plans` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL,
    `stripe_price_id` VARCHAR(255) NOT NULL,
    `price_cents` INT NOT NULL,
    `billing_interval` ENUM('monthly', 'yearly') NOT NULL,
    `features` JSON DEFAULT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_subscription_plans_slug` (`slug`),
    KEY `ix_subscription_plans_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Lounges Table
CREATE TABLE `lounges` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `mentor_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `category_id` INT DEFAULT NULL,
    `access_type` ENUM('free', 'paid', 'invite_only') NOT NULL DEFAULT 'free',
    `plan_id` INT DEFAULT NULL,
    `max_members` INT DEFAULT NULL,
    `is_public_listing` TINYINT(1) NOT NULL DEFAULT 1,
    `profile_image_id` INT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_lounges_slug` (`slug`),
    KEY `ix_lounges_id` (`id`),
    KEY `fk_lounge_mentor` (`mentor_id`),
    KEY `fk_lounge_category` (`category_id`),
    KEY `fk_lounge_plan` (`plan_id`),
    KEY `fk_lounge_profile_image` (`profile_image_id`),
    CONSTRAINT `fk_lounge_mentor` FOREIGN KEY (`mentor_id`) REFERENCES `mentors` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_lounge_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_lounge_plan` FOREIGN KEY (`plan_id`) REFERENCES `subscription_plans` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_lounge_profile_image` FOREIGN KEY (`profile_image_id`) REFERENCES `files` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Lounge Memberships Table
CREATE TABLE `lounge_memberships` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `lounge_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `role` ENUM('member', 'co_mentor') NOT NULL DEFAULT 'member',
    `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `left_at` DATETIME DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_lounge_memberships_id` (`id`),
    KEY `fk_membership_lounge` (`lounge_id`),
    KEY `fk_membership_user` (`user_id`),
    CONSTRAINT `fk_membership_lounge` FOREIGN KEY (`lounge_id`) REFERENCES `lounges` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_membership_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chat Threads Table
CREATE TABLE `chat_threads` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `lounge_id` INT DEFAULT NULL,
    `title` VARCHAR(255) DEFAULT NULL,
    `status` ENUM('open', 'archived') NOT NULL DEFAULT 'open',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_chat_threads_id` (`id`),
    KEY `fk_thread_user` (`user_id`),
    KEY `fk_thread_lounge` (`lounge_id`),
    CONSTRAINT `fk_thread_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_thread_lounge` FOREIGN KEY (`lounge_id`) REFERENCES `lounges` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chat Messages Table
CREATE TABLE `chat_messages` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `thread_id` INT NOT NULL,
    `sender_type` ENUM('user', 'ai', 'mentor') NOT NULL,
    `user_id` INT DEFAULT NULL,
    `content` TEXT NOT NULL,
    `message_metadata` JSON DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_chat_messages_id` (`id`),
    KEY `fk_message_thread` (`thread_id`),
    KEY `fk_message_user` (`user_id`),
    CONSTRAINT `fk_message_thread` FOREIGN KEY (`thread_id`) REFERENCES `chat_threads` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_message_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Message Attachments Table
CREATE TABLE `message_attachments` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `message_id` INT NOT NULL,
    `file_id` INT NOT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_message_attachments_id` (`id`),
    KEY `fk_attachment_message` (`message_id`),
    KEY `fk_attachment_file` (`file_id`),
    CONSTRAINT `fk_attachment_message` FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_attachment_file` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Notes Table
CREATE TABLE `notes` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `is_pinned` TINYINT(1) NOT NULL DEFAULT 0,
    `is_included_in_rag` TINYINT(1) NOT NULL DEFAULT 0,
    `tags` JSON DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_notes_id` (`id`),
    KEY `fk_note_user` (`user_id`),
    CONSTRAINT `fk_note_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Time Capsules Table
CREATE TABLE `time_capsules` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `unlock_at` DATETIME NOT NULL,
    `status` ENUM('locked', 'unlocked', 'expired') NOT NULL DEFAULT 'locked',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_time_capsules_id` (`id`),
    KEY `fk_capsule_user` (`user_id`),
    CONSTRAINT `fk_capsule_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Subscriptions Table
CREATE TABLE `subscriptions` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `plan_id` INT NOT NULL,
    `stripe_subscription_id` VARCHAR(255) NOT NULL,
    `status` ENUM('trialing', 'active', 'past_due', 'canceled') NOT NULL DEFAULT 'trialing',
    `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `renews_at` DATETIME NOT NULL,
    `canceled_at` DATETIME DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_subscriptions_stripe_id` (`stripe_subscription_id`),
    KEY `ix_subscriptions_id` (`id`),
    KEY `fk_subscription_user` (`user_id`),
    KEY `fk_subscription_plan` (`plan_id`),
    CONSTRAINT `fk_subscription_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_subscription_plan` FOREIGN KEY (`plan_id`) REFERENCES `subscription_plans` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Payments Table
CREATE TABLE `payments` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `provider` ENUM('stripe', 'klarna', 'afterpay') NOT NULL,
    `provider_payment_id` VARCHAR(255) NOT NULL,
    `amount_cents` INT NOT NULL,
    `currency` VARCHAR(3) NOT NULL DEFAULT 'USD',
    `status` ENUM('pending', 'succeeded', 'failed') NOT NULL DEFAULT 'pending',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_payments_provider_id` (`provider_payment_id`),
    KEY `ix_payments_id` (`id`),
    KEY `fk_payment_user` (`user_id`),
    CONSTRAINT `fk_payment_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Notifications Table
CREATE TABLE `notifications` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `type` VARCHAR(100) NOT NULL,
    `data` JSON DEFAULT NULL,
    `channel` ENUM('email', 'in_app') NOT NULL DEFAULT 'in_app',
    `status` ENUM('queued', 'sent', 'read') NOT NULL DEFAULT 'queued',
    `sent_at` DATETIME DEFAULT NULL,
    `read_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_notifications_id` (`id`),
    KEY `fk_notification_user` (`user_id`),
    CONSTRAINT `fk_notification_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Static Pages Table
CREATE TABLE `static_pages` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `slug` VARCHAR(255) NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `is_published` TINYINT(1) NOT NULL DEFAULT 0,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_static_pages_slug` (`slug`),
    KEY `ix_static_pages_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- FAQs Table
CREATE TABLE `faqs` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `category` VARCHAR(100) NOT NULL,
    `question` TEXT NOT NULL,
    `answer` TEXT NOT NULL,
    `sort_order` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `ix_faqs_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Compliance Requests Table
CREATE TABLE `compliance_requests` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `request_type` ENUM('export', 'delete') NOT NULL,
    `status` ENUM('pending', 'processing', 'done', 'rejected') NOT NULL DEFAULT 'pending',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_compliance_requests_id` (`id`),
    KEY `fk_compliance_user` (`user_id`),
    CONSTRAINT `fk_compliance_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Knowledge Base Categories Table
CREATE TABLE `kb_categories` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `lounge_id` INT DEFAULT NULL,
    `name` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `icon` VARCHAR(100) DEFAULT NULL,
    `sort_order` INT NOT NULL DEFAULT 0,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_kb_categories_id` (`id`),
    KEY `ix_kb_categories_slug` (`slug`),
    KEY `ix_kb_categories_lounge` (`lounge_id`),
    CONSTRAINT `fk_kb_category_lounge` FOREIGN KEY (`lounge_id`) REFERENCES `lounges` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Knowledge Base Prompts Table
CREATE TABLE `kb_prompts` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `lounge_id` INT DEFAULT NULL,
    `category_id` INT DEFAULT NULL,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `description` TEXT DEFAULT NULL,
    `tags` JSON DEFAULT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `is_included_in_rag` TINYINT(1) NOT NULL DEFAULT 1,
    `usage_count` INT NOT NULL DEFAULT 0,
    `embedding` JSON DEFAULT NULL,
    `embedding_model` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `created_by_id` INT DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_kb_prompts_id` (`id`),
    KEY `ix_kb_prompts_lounge` (`lounge_id`),
    KEY `fk_kb_prompt_category` (`category_id`),
    KEY `fk_kb_prompt_creator` (`created_by_id`),
    CONSTRAINT `fk_kb_prompt_lounge` FOREIGN KEY (`lounge_id`) REFERENCES `lounges` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_kb_prompt_category` FOREIGN KEY (`category_id`) REFERENCES `kb_categories` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_kb_prompt_creator` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Knowledge Base Documents Table
CREATE TABLE `kb_documents` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `lounge_id` INT DEFAULT NULL,
    `category_id` INT DEFAULT NULL,
    `file_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `original_filename` VARCHAR(500) NOT NULL,
    `file_type` VARCHAR(50) NOT NULL,
    `file_size_bytes` BIGINT NOT NULL,
    `extracted_text` TEXT DEFAULT NULL,
    `summary` TEXT DEFAULT NULL,
    `tags` JSON DEFAULT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `is_processed` TINYINT(1) NOT NULL DEFAULT 0,
    `processing_error` TEXT DEFAULT NULL,
    `embedding` JSON DEFAULT NULL,
    `embedding_model` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `created_by_id` INT DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_kb_documents_id` (`id`),
    KEY `ix_kb_documents_lounge` (`lounge_id`),
    KEY `fk_kb_document_category` (`category_id`),
    KEY `fk_kb_document_file` (`file_id`),
    KEY `fk_kb_document_creator` (`created_by_id`),
    CONSTRAINT `fk_kb_document_lounge` FOREIGN KEY (`lounge_id`) REFERENCES `lounges` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_kb_document_category` FOREIGN KEY (`category_id`) REFERENCES `kb_categories` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_kb_document_file` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_kb_document_creator` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Knowledge Base Document Chunks Table
CREATE TABLE `kb_document_chunks` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `document_id` INT NOT NULL,
    `content` TEXT NOT NULL,
    `chunk_index` INT NOT NULL,
    `start_char` INT DEFAULT NULL,
    `end_char` INT DEFAULT NULL,
    `token_count` INT DEFAULT NULL,
    `embedding` JSON DEFAULT NULL,
    `embedding_model` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_kb_document_chunks_id` (`id`),
    KEY `fk_chunk_document` (`document_id`),
    CONSTRAINT `fk_chunk_document` FOREIGN KEY (`document_id`) REFERENCES `kb_documents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Knowledge Base FAQs Table
CREATE TABLE `kb_faqs` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `lounge_id` INT DEFAULT NULL,
    `category_id` INT DEFAULT NULL,
    `question` TEXT NOT NULL,
    `answer` TEXT NOT NULL,
    `tags` JSON DEFAULT NULL,
    `sort_order` INT NOT NULL DEFAULT 0,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `is_included_in_rag` TINYINT(1) NOT NULL DEFAULT 1,
    `view_count` INT NOT NULL DEFAULT 0,
    `helpful_count` INT NOT NULL DEFAULT 0,
    `not_helpful_count` INT NOT NULL DEFAULT 0,
    `embedding` JSON DEFAULT NULL,
    `embedding_model` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `created_by_id` INT DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_kb_faqs_id` (`id`),
    KEY `ix_kb_faqs_lounge` (`lounge_id`),
    KEY `fk_kb_faq_category` (`category_id`),
    KEY `fk_kb_faq_creator` (`created_by_id`),
    CONSTRAINT `fk_kb_faq_lounge` FOREIGN KEY (`lounge_id`) REFERENCES `lounges` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_kb_faq_category` FOREIGN KEY (`category_id`) REFERENCES `kb_categories` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_kb_faq_creator` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit Logs Table
CREATE TABLE `audit_logs` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT DEFAULT NULL,
    `action` VARCHAR(100) NOT NULL,
    `entity_type` VARCHAR(100) DEFAULT NULL,
    `entity_id` INT DEFAULT NULL,
    `ip_address` VARCHAR(45) DEFAULT NULL,
    `user_agent` VARCHAR(500) DEFAULT NULL,
    `changes` JSON DEFAULT NULL,
    `metadata` JSON DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_audit_logs_id` (`id`),
    KEY `ix_audit_logs_action` (`action`),
    KEY `fk_audit_user` (`user_id`),
    CONSTRAINT `fk_audit_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- System Settings Table
CREATE TABLE `system_settings` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `key` VARCHAR(100) NOT NULL,
    `value` TEXT DEFAULT NULL,
    `value_type` VARCHAR(20) NOT NULL DEFAULT 'string',
    `description` TEXT DEFAULT NULL,
    `is_public` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_system_settings_key` (`key`),
    KEY `ix_system_settings_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- INSERT SEED DATA
-- ============================================================

-- Insert Alembic Version
INSERT INTO `alembic_version` (`version_num`) VALUES ('42fb2bd0a668');

-- ============================================================
-- USERS (password for all: "password123" hashed with bcrypt)
-- ============================================================

INSERT INTO `users` (`id`, `email`, `password_hash`, `name`, `avatar_url`, `role`, `email_verified_at`, `created_at`) VALUES
-- Admin Users
(1, 'admin@prompterly.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'System Admin', 'https://ui-avatars.com/api/?name=System+Admin&background=6366f1&color=fff', 'admin', NOW(), NOW()),
(2, 'superadmin@prompterly.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Super Admin', 'https://ui-avatars.com/api/?name=Super+Admin&background=dc2626&color=fff', 'admin', NOW(), NOW()),

-- Mentor Users
(3, 'john.mentor@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'John Smith', 'https://ui-avatars.com/api/?name=John+Smith&background=10b981&color=fff', 'mentor', NOW(), NOW()),
(4, 'sarah.coach@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Sarah Johnson', 'https://ui-avatars.com/api/?name=Sarah+Johnson&background=f59e0b&color=fff', 'mentor', NOW(), NOW()),
(5, 'mike.trainer@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Mike Williams', 'https://ui-avatars.com/api/?name=Mike+Williams&background=3b82f6&color=fff', 'mentor', NOW(), NOW()),
(6, 'emma.expert@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Emma Davis', 'https://ui-avatars.com/api/?name=Emma+Davis&background=ec4899&color=fff', 'mentor', NOW(), NOW()),
(7, 'david.consultant@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'David Brown', 'https://ui-avatars.com/api/?name=David+Brown&background=8b5cf6&color=fff', 'mentor', NOW(), NOW()),

-- Regular Member Users
(8, 'alice@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Alice Cooper', 'https://ui-avatars.com/api/?name=Alice+Cooper&background=14b8a6&color=fff', 'member', NOW(), NOW()),
(9, 'bob@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Bob Wilson', 'https://ui-avatars.com/api/?name=Bob+Wilson&background=f97316&color=fff', 'member', NOW(), NOW()),
(10, 'carol@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Carol Martinez', 'https://ui-avatars.com/api/?name=Carol+Martinez&background=06b6d4&color=fff', 'member', NOW(), NOW()),
(11, 'daniel@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Daniel Lee', 'https://ui-avatars.com/api/?name=Daniel+Lee&background=84cc16&color=fff', 'member', NOW(), NOW()),
(12, 'eve@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Eve Anderson', 'https://ui-avatars.com/api/?name=Eve+Anderson&background=a855f7&color=fff', 'member', NOW(), NOW()),
(13, 'frank@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Frank Thomas', 'https://ui-avatars.com/api/?name=Frank+Thomas&background=ef4444&color=fff', 'member', NOW(), NOW()),
(14, 'grace@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Grace Kim', 'https://ui-avatars.com/api/?name=Grace+Kim&background=22c55e&color=fff', 'member', NOW(), NOW()),
(15, 'henry@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Henry Garcia', 'https://ui-avatars.com/api/?name=Henry+Garcia&background=0ea5e9&color=fff', 'member', NOW(), NOW()),
(16, 'isabella@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Isabella Rodriguez', 'https://ui-avatars.com/api/?name=Isabella+Rodriguez&background=d946ef&color=fff', 'member', NOW(), NOW()),
(17, 'jack@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Jack Murphy', 'https://ui-avatars.com/api/?name=Jack+Murphy&background=eab308&color=fff', 'member', NOW(), NOW()),

-- Pending mentor (not yet approved)
(18, 'pending.mentor@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Pending Mentor', 'https://ui-avatars.com/api/?name=Pending+Mentor&background=94a3b8&color=fff', 'mentor', NOW(), NOW()),

-- Unverified user
(19, 'unverified@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Unverified User', 'https://ui-avatars.com/api/?name=Unverified+User&background=cbd5e1&color=333', 'member', NULL, NOW()),
(20, 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NQPZvZC1CwKJAm', 'Test User', 'https://ui-avatars.com/api/?name=Test+User&background=475569&color=fff', 'member', NOW(), NOW());

-- ============================================================
-- CATEGORIES
-- ============================================================

INSERT INTO `categories` (`id`, `name`, `slug`) VALUES
(1, 'Personal Development', 'personal-development'),
(2, 'Career Growth', 'career-growth'),
(3, 'Health & Wellness', 'health-wellness'),
(4, 'Business & Entrepreneurship', 'business-entrepreneurship'),
(5, 'Technology & Programming', 'technology-programming'),
(6, 'Finance & Investing', 'finance-investing'),
(7, 'Relationships', 'relationships'),
(8, 'Creativity & Arts', 'creativity-arts'),
(9, 'Leadership', 'leadership'),
(10, 'Mindfulness & Meditation', 'mindfulness-meditation');

-- ============================================================
-- MENTORS
-- ============================================================

INSERT INTO `mentors` (`id`, `user_id`, `headline`, `bio`, `intro_video_url`, `experience_years`, `status`, `created_at`) VALUES
(1, 3, 'Executive Coach & Leadership Expert', 'John Smith is a certified executive coach with over 15 years of experience helping leaders reach their full potential. He has worked with Fortune 500 companies and helped hundreds of professionals advance their careers.', 'https://www.youtube.com/watch?v=example1', 15, 'approved', NOW()),
(2, 4, 'Life Coach & Wellness Advocate', 'Sarah Johnson specializes in holistic life coaching, combining traditional coaching methods with mindfulness practices. She helps clients achieve balance in all areas of their lives.', 'https://www.youtube.com/watch?v=example2', 10, 'approved', NOW()),
(3, 5, 'Tech Career Mentor & Software Architect', 'Mike Williams is a seasoned software architect who has transitioned from developer to tech leader. He mentors aspiring developers and tech professionals on career growth in the technology industry.', 'https://www.youtube.com/watch?v=example3', 12, 'approved', NOW()),
(4, 6, 'Business Strategist & Startup Advisor', 'Emma Davis has founded three successful startups and now advises entrepreneurs on business strategy, fundraising, and scaling. She has helped over 50 startups reach their Series A funding.', 'https://www.youtube.com/watch?v=example4', 8, 'approved', NOW()),
(5, 7, 'Financial Advisor & Investment Coach', 'David Brown is a certified financial planner who specializes in helping individuals and families build wealth through smart investing and financial planning strategies.', 'https://www.youtube.com/watch?v=example5', 20, 'approved', NOW()),
(6, 18, 'Aspiring Fitness Coach', 'A passionate fitness enthusiast looking to become a certified coach.', NULL, 2, 'pending', NOW());

-- ============================================================
-- SUBSCRIPTION PLANS
-- ============================================================

INSERT INTO `subscription_plans` (`id`, `name`, `slug`, `stripe_price_id`, `price_cents`, `billing_interval`, `features`, `is_active`) VALUES
(1, 'Basic Monthly', 'basic-monthly', 'price_basic_monthly_123', 999, 'monthly', '["Access to public lounges", "Basic AI chat", "5 notes storage", "Email support"]', 1),
(2, 'Basic Yearly', 'basic-yearly', 'price_basic_yearly_123', 9990, 'yearly', '["Access to public lounges", "Basic AI chat", "5 notes storage", "Email support", "2 months free"]', 1),
(3, 'Pro Monthly', 'pro-monthly', 'price_pro_monthly_123', 2499, 'monthly', '["Access to all lounges", "Advanced AI chat", "Unlimited notes", "Priority support", "Time capsules", "RAG integration"]', 1),
(4, 'Pro Yearly', 'pro-yearly', 'price_pro_yearly_123', 24990, 'yearly', '["Access to all lounges", "Advanced AI chat", "Unlimited notes", "Priority support", "Time capsules", "RAG integration", "2 months free"]', 1),
(5, 'Premium Monthly', 'premium-monthly', 'price_premium_monthly_123', 4999, 'monthly', '["Everything in Pro", "1-on-1 mentor sessions", "Custom AI training", "White-glove onboarding", "Dedicated account manager"]', 1),
(6, 'Premium Yearly', 'premium-yearly', 'price_premium_yearly_123', 49990, 'yearly', '["Everything in Pro", "1-on-1 mentor sessions", "Custom AI training", "White-glove onboarding", "Dedicated account manager", "2 months free"]', 1);

-- ============================================================
-- LOUNGES
-- ============================================================

INSERT INTO `lounges` (`id`, `mentor_id`, `title`, `slug`, `description`, `category_id`, `access_type`, `plan_id`, `max_members`, `is_public_listing`, `created_at`) VALUES
(1, 1, 'Leadership Mastery', 'leadership-mastery', 'Learn the art of effective leadership from an executive coach. This lounge covers leadership styles, team management, and executive presence.', 9, 'free', NULL, 100, 1, NOW()),
(2, 1, 'Career Acceleration Lab', 'career-acceleration-lab', 'Fast-track your career with proven strategies for advancement, networking, and personal branding.', 2, 'paid', 3, 50, 1, NOW()),
(3, 2, 'Mindful Living Circle', 'mindful-living-circle', 'A supportive community for those seeking balance through mindfulness, meditation, and intentional living.', 10, 'free', NULL, NULL, 1, NOW()),
(4, 2, 'Wellness Transformation', 'wellness-transformation', 'Comprehensive wellness coaching covering nutrition, exercise, sleep, and mental health.', 3, 'paid', 3, 30, 1, NOW()),
(5, 3, 'Code to Career', 'code-to-career', 'For developers looking to level up their careers. Covers technical interviews, system design, and career planning.', 5, 'free', NULL, 200, 1, NOW()),
(6, 3, 'Tech Leadership Track', 'tech-leadership-track', 'Transition from developer to tech leader. Learn engineering management, architecture, and team building.', 5, 'paid', 5, 25, 1, NOW()),
(7, 4, 'Startup Founders Hub', 'startup-founders-hub', 'A community for startup founders to share experiences, get advice, and connect with other entrepreneurs.', 4, 'free', NULL, 150, 1, NOW()),
(8, 4, 'Fundraising Bootcamp', 'fundraising-bootcamp', 'Master the art of fundraising. Learn pitch decks, investor relations, and term sheet negotiations.', 4, 'paid', 5, 20, 0, NOW()),
(9, 5, 'Wealth Building 101', 'wealth-building-101', 'Learn the fundamentals of personal finance, investing, and building long-term wealth.', 6, 'free', NULL, NULL, 1, NOW()),
(10, 5, 'Investment Masterclass', 'investment-masterclass', 'Advanced investment strategies for those serious about growing their portfolio.', 6, 'invite_only', NULL, 15, 0, NOW());

-- ============================================================
-- LOUNGE MEMBERSHIPS
-- ============================================================

INSERT INTO `lounge_memberships` (`id`, `lounge_id`, `user_id`, `role`, `joined_at`, `left_at`) VALUES
-- Leadership Mastery (Lounge 1) members
(1, 1, 8, 'member', DATE_SUB(NOW(), INTERVAL 30 DAY), NULL),
(2, 1, 9, 'member', DATE_SUB(NOW(), INTERVAL 25 DAY), NULL),
(3, 1, 10, 'member', DATE_SUB(NOW(), INTERVAL 20 DAY), NULL),
(4, 1, 11, 'co_mentor', DATE_SUB(NOW(), INTERVAL 15 DAY), NULL),

-- Mindful Living Circle (Lounge 3) members
(5, 3, 8, 'member', DATE_SUB(NOW(), INTERVAL 45 DAY), NULL),
(6, 3, 12, 'member', DATE_SUB(NOW(), INTERVAL 40 DAY), NULL),
(7, 3, 13, 'member', DATE_SUB(NOW(), INTERVAL 35 DAY), NULL),
(8, 3, 14, 'member', DATE_SUB(NOW(), INTERVAL 30 DAY), NULL),
(9, 3, 15, 'member', DATE_SUB(NOW(), INTERVAL 25 DAY), NULL),

-- Code to Career (Lounge 5) members
(10, 5, 9, 'member', DATE_SUB(NOW(), INTERVAL 60 DAY), NULL),
(11, 5, 10, 'member', DATE_SUB(NOW(), INTERVAL 55 DAY), NULL),
(12, 5, 11, 'member', DATE_SUB(NOW(), INTERVAL 50 DAY), NULL),
(13, 5, 16, 'member', DATE_SUB(NOW(), INTERVAL 45 DAY), NULL),
(14, 5, 17, 'member', DATE_SUB(NOW(), INTERVAL 40 DAY), NULL),
(15, 5, 20, 'member', DATE_SUB(NOW(), INTERVAL 35 DAY), NULL),

-- Startup Founders Hub (Lounge 7) members
(16, 7, 12, 'member', DATE_SUB(NOW(), INTERVAL 90 DAY), NULL),
(17, 7, 13, 'member', DATE_SUB(NOW(), INTERVAL 85 DAY), NULL),
(18, 7, 14, 'member', DATE_SUB(NOW(), INTERVAL 80 DAY), NULL),

-- Wealth Building 101 (Lounge 9) members
(19, 9, 8, 'member', DATE_SUB(NOW(), INTERVAL 100 DAY), NULL),
(20, 9, 15, 'member', DATE_SUB(NOW(), INTERVAL 95 DAY), NULL),
(21, 9, 16, 'member', DATE_SUB(NOW(), INTERVAL 90 DAY), NULL),
(22, 9, 17, 'member', DATE_SUB(NOW(), INTERVAL 85 DAY), NULL),

-- Left memberships (historical)
(23, 1, 15, 'member', DATE_SUB(NOW(), INTERVAL 60 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY)),
(24, 3, 17, 'member', DATE_SUB(NOW(), INTERVAL 50 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY));

-- ============================================================
-- CHAT THREADS
-- ============================================================

INSERT INTO `chat_threads` (`id`, `user_id`, `lounge_id`, `title`, `status`, `created_at`) VALUES
-- General AI chats (no lounge)
(1, 8, NULL, 'Getting started with Prompterly', 'open', DATE_SUB(NOW(), INTERVAL 20 DAY)),
(2, 9, NULL, 'Career advice needed', 'open', DATE_SUB(NOW(), INTERVAL 15 DAY)),
(3, 10, NULL, 'Daily reflection', 'open', DATE_SUB(NOW(), INTERVAL 10 DAY)),
(4, 11, NULL, 'Goal setting session', 'archived', DATE_SUB(NOW(), INTERVAL 30 DAY)),

-- Lounge-specific chats
(5, 8, 1, 'Leadership challenges discussion', 'open', DATE_SUB(NOW(), INTERVAL 25 DAY)),
(6, 9, 5, 'Interview preparation', 'open', DATE_SUB(NOW(), INTERVAL 18 DAY)),
(7, 12, 3, 'Meditation techniques', 'open', DATE_SUB(NOW(), INTERVAL 12 DAY)),
(8, 12, 7, 'Startup idea validation', 'open', DATE_SUB(NOW(), INTERVAL 8 DAY)),
(9, 15, 9, 'Investment portfolio review', 'open', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(10, 20, 5, 'Code review discussion', 'open', DATE_SUB(NOW(), INTERVAL 3 DAY));

-- ============================================================
-- CHAT MESSAGES
-- ============================================================

INSERT INTO `chat_messages` (`id`, `thread_id`, `sender_type`, `user_id`, `content`, `message_metadata`, `created_at`) VALUES
-- Thread 1: Getting started with Prompterly
(1, 1, 'user', 8, 'Hi! I just joined Prompterly. Can you help me understand how to get the most out of this platform?', NULL, DATE_SUB(NOW(), INTERVAL 20 DAY)),
(2, 1, 'ai', NULL, 'Welcome to Prompterly! I''d be happy to help you get started. Here are some key features:\n\n1. **Lounges**: Join coaching spaces led by expert mentors\n2. **AI Chat**: I''m here to help you 24/7 with guidance and support\n3. **Notes**: Keep track of your thoughts and insights\n4. **Time Capsules**: Send messages to your future self\n\nWhat area would you like to explore first?', '{"model": "gpt-4", "tokens": 150}', DATE_SUB(NOW(), INTERVAL 20 DAY)),
(3, 1, 'user', 8, 'I''m interested in leadership development. Which lounges would you recommend?', NULL, DATE_SUB(NOW(), INTERVAL 19 DAY)),
(4, 1, 'ai', NULL, 'Great choice! For leadership development, I''d recommend:\n\n1. **Leadership Mastery** by John Smith - Free lounge covering leadership fundamentals\n2. **Career Acceleration Lab** - Premium lounge for career advancement strategies\n\nJohn Smith has 15 years of executive coaching experience. Would you like me to tell you more about either of these?', '{"model": "gpt-4", "tokens": 120}', DATE_SUB(NOW(), INTERVAL 19 DAY)),

-- Thread 2: Career advice needed
(5, 2, 'user', 9, 'I''m thinking about switching from software development to product management. What should I consider?', NULL, DATE_SUB(NOW(), INTERVAL 15 DAY)),
(6, 2, 'ai', NULL, 'That''s an exciting career transition! Here are key considerations:\n\n**Skills to Develop:**\n- Product strategy and roadmapping\n- Stakeholder management\n- Data analysis and metrics\n- User research methodologies\n\n**Advantages of Your Background:**\n- Technical credibility with engineering teams\n- Understanding of development processes\n- Ability to communicate with developers effectively\n\n**Steps to Transition:**\n1. Take on PM-adjacent responsibilities in your current role\n2. Build a portfolio of product thinking\n3. Network with PMs in your organization\n\nWould you like to dive deeper into any of these areas?', '{"model": "gpt-4", "tokens": 200}', DATE_SUB(NOW(), INTERVAL 15 DAY)),

-- Thread 5: Leadership challenges discussion (in lounge)
(7, 5, 'user', 8, 'I''m struggling with a team member who seems disengaged. How should I approach this?', NULL, DATE_SUB(NOW(), INTERVAL 25 DAY)),
(8, 5, 'ai', NULL, 'Dealing with disengaged team members requires empathy and strategic thinking. Here''s a framework:\n\n**Step 1: Observe & Document**\n- Note specific behaviors, not assumptions\n- Consider timing - when did this start?\n\n**Step 2: Private Conversation**\n- Schedule a 1-on-1 in a neutral setting\n- Lead with curiosity, not accusation\n- Ask open-ended questions: "How are you feeling about your work lately?"\n\n**Step 3: Listen & Understand**\n- There might be personal issues, burnout, or role mismatch\n- Don''t interrupt or jump to solutions\n\n**Step 4: Co-create Solutions**\n- Involve them in finding the path forward\n- Set clear expectations and check-ins\n\nWould you like to role-play this conversation?', '{"model": "gpt-4", "tokens": 250}', DATE_SUB(NOW(), INTERVAL 25 DAY)),
(9, 5, 'mentor', 3, 'Great advice from the AI! I''d add that sometimes disengagement signals a need for growth. Consider whether they need new challenges or learning opportunities.', NULL, DATE_SUB(NOW(), INTERVAL 24 DAY)),

-- Thread 6: Interview preparation
(10, 6, 'user', 9, 'I have a system design interview coming up. Can you help me prepare?', NULL, DATE_SUB(NOW(), INTERVAL 18 DAY)),
(11, 6, 'ai', NULL, 'Absolutely! System design interviews assess your ability to design scalable systems. Here''s a structured approach:\n\n**Framework (RESHADED):**\n- **R**equirements clarification\n- **E**stimations (traffic, storage)\n- **S**torage schema design\n- **H**igh-level design\n- **A**PI design\n- **D**etailed component design\n- **E**valuate and iterate\n- **D**iscuss trade-offs\n\n**Common Topics:**\n- URL shortener\n- Rate limiter\n- Chat system\n- News feed\n- Search autocomplete\n\nWhich topic would you like to practice?', '{"model": "gpt-4", "tokens": 180}', DATE_SUB(NOW(), INTERVAL 18 DAY)),
(12, 6, 'user', 9, 'Let''s practice designing a URL shortener!', NULL, DATE_SUB(NOW(), INTERVAL 17 DAY)),
(13, 6, 'ai', NULL, 'Perfect! Let''s design a URL shortener like bit.ly.\n\n**First, let''s clarify requirements:**\n\nFunctional:\n- Shorten long URLs\n- Redirect short URLs to original\n- Custom aliases (optional)\n- Analytics (optional)\n\nNon-functional:\n- High availability\n- Low latency redirects\n- Scalability (100M URLs/day)\n\n**Questions for you:**\n1. What''s the expected ratio of reads to writes?\n2. How long should URLs be stored?\n3. Do we need analytics?\n\nTake your time to think through these!', '{"model": "gpt-4", "tokens": 160}', DATE_SUB(NOW(), INTERVAL 17 DAY));

-- ============================================================
-- NOTES
-- ============================================================

INSERT INTO `notes` (`id`, `user_id`, `title`, `content`, `is_pinned`, `is_included_in_rag`, `tags`, `created_at`) VALUES
(1, 8, 'Leadership Principles', 'Key leadership principles I''ve learned:\n\n1. Lead by example\n2. Listen more than you speak\n3. Give credit to the team\n4. Take responsibility for failures\n5. Invest in people''s growth', 1, 1, '["leadership", "principles", "growth"]', DATE_SUB(NOW(), INTERVAL 25 DAY)),
(2, 8, 'Book Notes: Atomic Habits', 'Main takeaways from Atomic Habits by James Clear:\n\n- Habits are the compound interest of self-improvement\n- Focus on systems, not goals\n- The 4 laws: Make it obvious, attractive, easy, satisfying\n- Identity-based habits are more powerful', 0, 1, '["books", "habits", "productivity"]', DATE_SUB(NOW(), INTERVAL 20 DAY)),
(3, 9, 'Interview Prep Checklist', '## Technical Interview Prep\n\n- [ ] Review data structures\n- [ ] Practice LeetCode medium problems\n- [ ] System design fundamentals\n- [ ] Behavioral questions (STAR method)\n- [ ] Research the company', 1, 0, '["career", "interview", "checklist"]', DATE_SUB(NOW(), INTERVAL 15 DAY)),
(4, 10, 'Daily Gratitude', 'Things I''m grateful for today:\n\n1. My supportive family\n2. Good health\n3. Opportunities to learn\n4. This beautiful weather\n5. A meaningful job', 0, 0, '["gratitude", "mindfulness", "daily"]', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(5, 11, 'Goal Setting Framework', 'Using the SMART framework:\n\n**S**pecific - What exactly do I want?\n**M**easurable - How will I track progress?\n**A**chievable - Is this realistic?\n**R**elevant - Does this align with my values?\n**T**ime-bound - What''s the deadline?', 1, 1, '["goals", "framework", "planning"]', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(6, 12, 'Meditation Journal', 'Today''s meditation (20 minutes):\n\nFocused on breath awareness. Mind wandered frequently but gently returned focus each time. Feeling calmer and more centered. Will try body scan tomorrow.', 0, 0, '["meditation", "mindfulness", "journal"]', DATE_SUB(NOW(), INTERVAL 2 DAY)),
(7, 15, 'Investment Notes', 'Portfolio allocation strategy:\n\n- 60% Index funds (VTI, VXUS)\n- 20% Bonds (BND)\n- 10% REITs\n- 10% Individual stocks\n\nRebalance quarterly. Stay the course during volatility.', 1, 1, '["investing", "portfolio", "strategy"]', DATE_SUB(NOW(), INTERVAL 40 DAY));

-- ============================================================
-- TIME CAPSULES
-- ============================================================

INSERT INTO `time_capsules` (`id`, `user_id`, `title`, `content`, `unlock_at`, `status`, `created_at`) VALUES
(1, 8, 'Letter to Future Me - 1 Year', 'Dear Future Me,\n\nI hope you''ve made progress on your leadership journey. Remember why you started this path. Stay humble, keep learning, and never stop growing.\n\nWith hope,\nPast You', DATE_ADD(NOW(), INTERVAL 1 YEAR), 'locked', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(2, 9, 'Career Goals Check-in', 'By the time you read this, you should have:\n\n1. Completed the PM transition\n2. Led at least one product launch\n3. Built a network of 50+ PM connections\n\nDid you do it?', DATE_ADD(NOW(), INTERVAL 6 MONTH), 'locked', DATE_SUB(NOW(), INTERVAL 15 DAY)),
(3, 10, 'New Year Reflection', 'This was a year of growth. I learned to be present, to appreciate small moments, and to let go of what I cannot control. Remember this feeling of peace.', DATE_SUB(NOW(), INTERVAL 5 DAY), 'unlocked', DATE_SUB(NOW(), INTERVAL 365 DAY)),
(4, 11, 'Birthday Message', 'Happy Birthday! You''ve come so far. Take a moment to celebrate your achievements and set new exciting goals for the year ahead!', DATE_ADD(NOW(), INTERVAL 3 MONTH), 'locked', DATE_SUB(NOW(), INTERVAL 10 DAY)),
(5, 12, 'Meditation Milestone', 'If you''re reading this, you''ve maintained your meditation practice for 6 months! Incredible dedication. How does your mind feel compared to when you started?', DATE_ADD(NOW(), INTERVAL 5 MONTH), 'locked', DATE_SUB(NOW(), INTERVAL 30 DAY));

-- ============================================================
-- SUBSCRIPTIONS
-- ============================================================

INSERT INTO `subscriptions` (`id`, `user_id`, `plan_id`, `stripe_subscription_id`, `status`, `started_at`, `renews_at`, `canceled_at`) VALUES
(1, 8, 3, 'sub_alice_pro_001', 'active', DATE_SUB(NOW(), INTERVAL 60 DAY), DATE_ADD(NOW(), INTERVAL 30 DAY), NULL),
(2, 9, 4, 'sub_bob_pro_yearly_001', 'active', DATE_SUB(NOW(), INTERVAL 180 DAY), DATE_ADD(NOW(), INTERVAL 185 DAY), NULL),
(3, 10, 1, 'sub_carol_basic_001', 'active', DATE_SUB(NOW(), INTERVAL 45 DAY), DATE_ADD(NOW(), INTERVAL 15 DAY), NULL),
(4, 11, 5, 'sub_daniel_premium_001', 'active', DATE_SUB(NOW(), INTERVAL 30 DAY), DATE_ADD(NOW(), INTERVAL 30 DAY), NULL),
(5, 12, 3, 'sub_eve_pro_001', 'past_due', DATE_SUB(NOW(), INTERVAL 90 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY), NULL),
(6, 13, 1, 'sub_frank_basic_001', 'canceled', DATE_SUB(NOW(), INTERVAL 120 DAY), DATE_SUB(NOW(), INTERVAL 30 DAY), DATE_SUB(NOW(), INTERVAL 35 DAY));

-- ============================================================
-- PAYMENTS
-- ============================================================

INSERT INTO `payments` (`id`, `user_id`, `provider`, `provider_payment_id`, `amount_cents`, `currency`, `status`, `created_at`) VALUES
(1, 8, 'stripe', 'pi_alice_001', 2499, 'USD', 'succeeded', DATE_SUB(NOW(), INTERVAL 60 DAY)),
(2, 8, 'stripe', 'pi_alice_002', 2499, 'USD', 'succeeded', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(3, 9, 'stripe', 'pi_bob_001', 24990, 'USD', 'succeeded', DATE_SUB(NOW(), INTERVAL 180 DAY)),
(4, 10, 'stripe', 'pi_carol_001', 999, 'USD', 'succeeded', DATE_SUB(NOW(), INTERVAL 45 DAY)),
(5, 11, 'stripe', 'pi_daniel_001', 4999, 'USD', 'succeeded', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(6, 12, 'stripe', 'pi_eve_001', 2499, 'USD', 'succeeded', DATE_SUB(NOW(), INTERVAL 90 DAY)),
(7, 12, 'stripe', 'pi_eve_002', 2499, 'USD', 'failed', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(8, 13, 'stripe', 'pi_frank_001', 999, 'USD', 'succeeded', DATE_SUB(NOW(), INTERVAL 120 DAY));

-- ============================================================
-- NOTIFICATIONS
-- ============================================================

INSERT INTO `notifications` (`id`, `user_id`, `type`, `data`, `channel`, `status`, `sent_at`, `read_at`, `created_at`) VALUES
(1, 8, 'welcome', '{"message": "Welcome to Prompterly!"}', 'in_app', 'read', NOW(), DATE_SUB(NOW(), INTERVAL 29 DAY), DATE_SUB(NOW(), INTERVAL 30 DAY)),
(2, 8, 'lounge_joined', '{"lounge_id": 1, "lounge_name": "Leadership Mastery"}', 'in_app', 'read', NOW(), DATE_SUB(NOW(), INTERVAL 29 DAY), DATE_SUB(NOW(), INTERVAL 30 DAY)),
(3, 9, 'welcome', '{"message": "Welcome to Prompterly!"}', 'in_app', 'read', NOW(), DATE_SUB(NOW(), INTERVAL 24 DAY), DATE_SUB(NOW(), INTERVAL 25 DAY)),
(4, 10, 'capsule_unlocked', '{"capsule_id": 3, "title": "New Year Reflection"}', 'in_app', 'sent', NOW(), NULL, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(5, 11, 'subscription_renewed', '{"plan": "Premium Monthly", "amount": "$49.99"}', 'email', 'sent', NOW(), NULL, NOW()),
(6, 12, 'payment_failed', '{"reason": "Card declined"}', 'email', 'sent', NOW(), NULL, DATE_SUB(NOW(), INTERVAL 5 DAY)),
(7, 8, 'new_message', '{"thread_id": 5, "preview": "Great advice from the AI..."}', 'in_app', 'queued', NULL, NULL, DATE_SUB(NOW(), INTERVAL 24 DAY));

-- ============================================================
-- STATIC PAGES
-- ============================================================

INSERT INTO `static_pages` (`id`, `slug`, `title`, `content`, `is_published`, `updated_at`) VALUES
(1, 'about', 'About Prompterly', '# About Prompterly\n\nPrompterly is an AI-powered coaching platform that connects you with expert mentors and intelligent AI assistants to help you achieve your personal and professional goals.\n\n## Our Mission\n\nTo democratize access to high-quality coaching and personal development resources through the power of AI and community.\n\n## Our Values\n\n- **Growth Mindset**: We believe everyone can improve and grow\n- **Accessibility**: World-class coaching should be available to all\n- **Privacy**: Your journey is personal, and we protect it\n- **Community**: Growth is better together', 1, NOW()),
(2, 'privacy-policy', 'Privacy Policy', '# Privacy Policy\n\nLast updated: December 2024\n\n## Information We Collect\n\nWe collect information you provide directly, including:\n- Account information (name, email)\n- Content you create (notes, messages)\n- Usage data\n\n## How We Use Your Information\n\nWe use your information to:\n- Provide and improve our services\n- Personalize your experience\n- Communicate with you\n\n## Data Security\n\nWe implement industry-standard security measures to protect your data.', 1, NOW()),
(3, 'terms-of-service', 'Terms of Service', '# Terms of Service\n\nLast updated: December 2024\n\n## Acceptance of Terms\n\nBy using Prompterly, you agree to these terms.\n\n## User Responsibilities\n\n- Maintain account security\n- Use the platform respectfully\n- Not share harmful content\n\n## Intellectual Property\n\nYour content remains yours. You grant us license to display it on the platform.', 1, NOW()),
(4, 'help', 'Help Center', '# Help Center\n\n## Getting Started\n\n1. Create your account\n2. Complete your profile\n3. Explore lounges\n4. Start chatting with AI\n\n## Common Questions\n\nSee our FAQ section for answers to common questions.\n\n## Contact Support\n\nEmail us at support@prompterly.com', 1, NOW()),
(5, 'careers', 'Careers at Prompterly', '# Join Our Team\n\nWe''re building the future of AI-powered coaching. Join us!\n\n## Open Positions\n\n- Senior Full Stack Developer\n- AI/ML Engineer\n- Product Designer\n- Customer Success Manager\n\n## Benefits\n\n- Competitive salary\n- Remote-first culture\n- Learning budget\n- Health benefits', 0, NOW());

-- ============================================================
-- FAQs
-- ============================================================

INSERT INTO `faqs` (`id`, `category`, `question`, `answer`, `sort_order`) VALUES
(1, 'General', 'What is Prompterly?', 'Prompterly is an AI-powered coaching platform that combines expert human mentors with intelligent AI assistants to help you achieve your goals in personal development, career growth, and more.', 1),
(2, 'General', 'How does the AI coaching work?', 'Our AI is trained on best practices in coaching and personal development. It can have conversations with you, provide guidance, and help you reflect on your journey. The AI learns from your interactions to provide more personalized support over time.', 2),
(3, 'General', 'Is my data private?', 'Yes, we take privacy seriously. Your conversations and notes are encrypted and only accessible to you. We never share your personal data with third parties without your consent.', 3),
(4, 'Pricing', 'What plans are available?', 'We offer Basic, Pro, and Premium plans. Basic gives you access to public lounges and basic AI chat. Pro unlocks all lounges and advanced features. Premium includes 1-on-1 mentor sessions.', 1),
(5, 'Pricing', 'Can I cancel my subscription?', 'Yes, you can cancel your subscription at any time. You''ll continue to have access until the end of your billing period.', 2),
(6, 'Pricing', 'Is there a free trial?', 'Yes! All new users get 14 days of free access to Pro features. No credit card required.', 3),
(7, 'Features', 'What are Lounges?', 'Lounges are themed coaching spaces created by expert mentors. Each lounge focuses on a specific topic like leadership, wellness, or career development. You can join discussions, get AI support, and connect with others on similar journeys.', 1),
(8, 'Features', 'What are Time Capsules?', 'Time Capsules let you write messages to your future self. You set an unlock date, and the message remains sealed until then. It''s a powerful tool for reflection and goal-setting.', 2),
(9, 'Features', 'How do Notes work?', 'Notes is your personal knowledge base. You can write notes, tag them, and optionally include them in your AI context so the AI can reference your thoughts when giving advice.', 3),
(10, 'Technical', 'What browsers are supported?', 'Prompterly works best on modern browsers: Chrome, Firefox, Safari, and Edge. We recommend keeping your browser updated for the best experience.', 1),
(11, 'Technical', 'Is there a mobile app?', 'We''re currently focused on our web experience, which is fully responsive on mobile devices. A dedicated mobile app is on our roadmap.', 2);

-- ============================================================
-- KNOWLEDGE BASE CATEGORIES
-- ============================================================

INSERT INTO `kb_categories` (`id`, `lounge_id`, `name`, `slug`, `description`, `icon`, `sort_order`, `is_active`, `created_at`) VALUES
-- Global KB categories
(1, NULL, 'Getting Started', 'getting-started', 'Essential guides for new users', 'rocket', 1, 1, NOW()),
(2, NULL, 'Best Practices', 'best-practices', 'Proven strategies and techniques', 'star', 2, 1, NOW()),
(3, NULL, 'Templates', 'templates', 'Ready-to-use templates and frameworks', 'file-text', 3, 1, NOW()),

-- Lounge-specific KB categories
(4, 1, 'Leadership Resources', 'leadership-resources', 'Curated resources for leaders', 'users', 1, 1, NOW()),
(5, 5, 'Coding Interview Prep', 'coding-interview-prep', 'Materials for technical interviews', 'code', 1, 1, NOW()),
(6, 7, 'Startup Toolkit', 'startup-toolkit', 'Essential resources for founders', 'briefcase', 1, 1, NOW());

-- ============================================================
-- KNOWLEDGE BASE PROMPTS
-- ============================================================

INSERT INTO `kb_prompts` (`id`, `lounge_id`, `category_id`, `title`, `content`, `description`, `tags`, `is_active`, `is_included_in_rag`, `usage_count`, `created_by_id`, `created_at`) VALUES
(1, NULL, 1, 'Goal Setting Framework', 'Help the user define SMART goals:\n\n1. Ask about their general goal\n2. Help make it Specific\n3. Define Measurable criteria\n4. Ensure it''s Achievable\n5. Confirm it''s Relevant to their values\n6. Set a Time-bound deadline\n\nEnd with a summary of the refined goal.', 'Guide users through SMART goal setting', '["goals", "planning", "framework"]', 1, 1, 45, 1, NOW()),
(2, NULL, 2, 'Daily Reflection', 'Guide the user through an evening reflection:\n\n1. What went well today?\n2. What could have been better?\n3. What did you learn?\n4. What are you grateful for?\n5. What''s one thing to focus on tomorrow?\n\nBe supportive and encouraging.', 'Evening reflection prompt', '["reflection", "mindfulness", "daily"]', 1, 1, 128, 1, NOW()),
(3, 1, 4, 'Leadership Style Assessment', 'Help the user understand their leadership style:\n\n1. Ask about how they make decisions (collaborative vs. decisive)\n2. How they handle conflict\n3. How they motivate their team\n4. Their communication preferences\n\nProvide insights on their likely leadership style (transformational, servant, etc.)', 'Discover your leadership style', '["leadership", "assessment", "self-awareness"]', 1, 1, 67, 3, NOW()),
(4, 5, 5, 'System Design Interview Prep', 'Guide the user through system design:\n\n1. Clarify requirements\n2. Estimate scale\n3. Design high-level architecture\n4. Deep dive into components\n5. Address bottlenecks\n6. Discuss trade-offs\n\nAsk probing questions like an interviewer would.', 'Practice system design interviews', '["interview", "system-design", "tech"]', 1, 1, 89, 5, NOW()),
(5, 7, 6, 'Pitch Deck Review', 'Help the founder improve their pitch deck:\n\n1. Problem - Is it clear and relatable?\n2. Solution - Is it compelling?\n3. Market - Is the opportunity big enough?\n4. Traction - What proof points exist?\n5. Team - Why this team?\n6. Ask - Is it specific?\n\nProvide constructive feedback.', 'Get feedback on your startup pitch', '["startup", "pitch", "fundraising"]', 1, 1, 34, 6, NOW());

-- ============================================================
-- KNOWLEDGE BASE FAQs
-- ============================================================

INSERT INTO `kb_faqs` (`id`, `lounge_id`, `category_id`, `question`, `answer`, `tags`, `sort_order`, `is_active`, `is_included_in_rag`, `view_count`, `helpful_count`, `not_helpful_count`, `created_by_id`, `created_at`) VALUES
(1, NULL, 1, 'How do I get started with coaching?', 'Start by exploring our free lounges to find topics that interest you. Join a lounge, introduce yourself, and start chatting with the AI assistant. The AI will guide you through setting goals and developing an action plan.', '["onboarding", "getting-started"]', 1, 1, 1, 234, 45, 3, 1, NOW()),
(2, NULL, 1, 'How often should I check in with the AI?', 'We recommend daily check-ins, even if just for 5 minutes. Consistency is key in personal development. You can do a quick morning intention or evening reflection.', '["frequency", "habits"]', 2, 1, 1, 156, 32, 5, 1, NOW()),
(3, 1, 4, 'What makes a good leader?', 'Good leaders combine several key traits:\n- Vision and strategic thinking\n- Emotional intelligence\n- Communication skills\n- Ability to develop others\n- Integrity and trustworthiness\n- Adaptability\n\nLeadership is a journey, not a destination.', '["leadership", "traits"]', 1, 1, 1, 89, 21, 2, 3, NOW()),
(4, 5, 5, 'How should I prepare for a coding interview?', 'A structured approach:\n1. **Data structures**: Arrays, trees, graphs, hash maps\n2. **Algorithms**: Sorting, searching, dynamic programming\n3. **Practice**: LeetCode medium problems (2-3 daily)\n4. **Mock interviews**: Practice with peers\n5. **System design**: For senior roles\n\nConsistency over intensity!', '["interview", "coding", "preparation"]', 1, 1, 1, 312, 78, 4, 5, NOW()),
(5, 7, 6, 'How much equity should I give to co-founders?', 'It depends on several factors:\n- Time commitment\n- Skills and experience\n- Capital contribution\n- Opportunity cost\n\nConsider vesting schedules (typically 4 years with 1-year cliff). Use frameworks like the Founder''s Pie Calculator for guidance. Always consult a lawyer.', '["equity", "co-founders", "startup"]', 1, 1, 1, 178, 42, 6, 6, NOW());

-- ============================================================
-- SYSTEM SETTINGS
-- ============================================================

INSERT INTO `system_settings` (`id`, `key`, `value`, `value_type`, `description`, `is_public`, `created_at`) VALUES
(1, 'maintenance_mode', 'false', 'bool', 'Enable maintenance mode', 0, NOW()),
(2, 'max_file_size_mb', '10', 'int', 'Maximum file upload size in MB', 1, NOW()),
(3, 'ai_model_default', 'gpt-4', 'string', 'Default AI model for chat', 0, NOW()),
(4, 'free_trial_days', '14', 'int', 'Number of free trial days', 1, NOW()),
(5, 'support_email', 'support@prompterly.com', 'string', 'Support email address', 1, NOW()),
(6, 'feature_flags', '{"new_onboarding": true, "beta_features": false}', 'json', 'Feature flags configuration', 0, NOW());

-- ============================================================
-- AUDIT LOGS (sample entries)
-- ============================================================

INSERT INTO `audit_logs` (`id`, `user_id`, `action`, `entity_type`, `entity_id`, `ip_address`, `user_agent`, `changes`, `metadata`, `created_at`) VALUES
(1, 1, 'user.created', 'user', 8, '192.168.1.1', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', NULL, '{"source": "registration"}', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(2, 8, 'lounge.joined', 'lounge_membership', 1, '192.168.1.2', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', NULL, '{"lounge_id": 1}', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(3, 1, 'mentor.approved', 'mentor', 1, '192.168.1.1', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', '{"status": {"from": "pending", "to": "approved"}}', NULL, DATE_SUB(NOW(), INTERVAL 60 DAY)),
(4, 8, 'subscription.created', 'subscription', 1, '192.168.1.2', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', NULL, '{"plan_id": 3}', DATE_SUB(NOW(), INTERVAL 60 DAY)),
(5, 1, 'lounge.created', 'lounge', 1, '192.168.1.1', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', NULL, '{"mentor_id": 1}', DATE_SUB(NOW(), INTERVAL 90 DAY));

-- ============================================================
-- COMPLETION
-- ============================================================

-- Reset auto-increment values to continue from last ID
ALTER TABLE `users` AUTO_INCREMENT = 21;
ALTER TABLE `categories` AUTO_INCREMENT = 11;
ALTER TABLE `mentors` AUTO_INCREMENT = 7;
ALTER TABLE `subscription_plans` AUTO_INCREMENT = 7;
ALTER TABLE `lounges` AUTO_INCREMENT = 11;
ALTER TABLE `lounge_memberships` AUTO_INCREMENT = 25;
ALTER TABLE `chat_threads` AUTO_INCREMENT = 11;
ALTER TABLE `chat_messages` AUTO_INCREMENT = 14;
ALTER TABLE `notes` AUTO_INCREMENT = 8;
ALTER TABLE `time_capsules` AUTO_INCREMENT = 6;
ALTER TABLE `subscriptions` AUTO_INCREMENT = 7;
ALTER TABLE `payments` AUTO_INCREMENT = 9;
ALTER TABLE `notifications` AUTO_INCREMENT = 8;
ALTER TABLE `static_pages` AUTO_INCREMENT = 6;
ALTER TABLE `faqs` AUTO_INCREMENT = 12;
ALTER TABLE `kb_categories` AUTO_INCREMENT = 7;
ALTER TABLE `kb_prompts` AUTO_INCREMENT = 6;
ALTER TABLE `kb_faqs` AUTO_INCREMENT = 6;
ALTER TABLE `system_settings` AUTO_INCREMENT = 7;
ALTER TABLE `audit_logs` AUTO_INCREMENT = 6;

SELECT 'Prompterly database initialized successfully!' AS status;
SELECT CONCAT('Total users: ', COUNT(*)) AS info FROM users;
SELECT CONCAT('Total mentors: ', COUNT(*)) AS info FROM mentors;
SELECT CONCAT('Total lounges: ', COUNT(*)) AS info FROM lounges;
SELECT CONCAT('Total memberships: ', COUNT(*)) AS info FROM lounge_memberships;
