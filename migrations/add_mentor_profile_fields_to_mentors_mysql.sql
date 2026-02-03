-- Migration: Add mentor profile fields to mentors table (MySQL)
-- Description: Adds fields for "More from Mentor" modal content
-- Date: 2026-02-02

-- Mentor profile fields for "More from Mentor" modal
ALTER TABLE mentors
    ADD COLUMN mentor_title VARCHAR(255) NULL COMMENT 'Mentor title displayed in modal (e.g., Mindset mentor)',
    ADD COLUMN philosophy TEXT NULL COMMENT 'Mentor philosophy/bio text',
    ADD COLUMN hobbies TEXT NULL COMMENT 'JSON array of hobbies/interests',

    -- Social links
    ADD COLUMN social_instagram VARCHAR(500) NULL COMMENT 'Instagram profile URL',
    ADD COLUMN social_tiktok VARCHAR(500) NULL COMMENT 'TikTok profile URL',
    ADD COLUMN social_linkedin VARCHAR(500) NULL COMMENT 'LinkedIn profile URL',
    ADD COLUMN social_youtube VARCHAR(500) NULL COMMENT 'YouTube channel URL',

    -- Book recommendation
    ADD COLUMN book_title VARCHAR(500) NULL COMMENT 'Recommended book title',
    ADD COLUMN book_description TEXT NULL COMMENT 'Book recommendation description',

    -- Podcast recommendation
    ADD COLUMN podcast_rec_title VARCHAR(500) NULL COMMENT 'Recommended podcast title',

    -- Podcast links (More from me section)
    ADD COLUMN podcast_name VARCHAR(255) NULL COMMENT 'Mentor own podcast name',
    ADD COLUMN podcast_youtube VARCHAR(500) NULL COMMENT 'Podcast YouTube URL',
    ADD COLUMN podcast_spotify VARCHAR(500) NULL COMMENT 'Podcast Spotify URL',
    ADD COLUMN podcast_apple VARCHAR(500) NULL COMMENT 'Podcast Apple Podcasts URL',

    -- Quick prompts
    ADD COLUMN quick_prompts TEXT NULL COMMENT 'JSON array of quick prompt strings';
