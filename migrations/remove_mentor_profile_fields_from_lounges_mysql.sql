-- Migration: Remove mentor profile fields from lounges table (MySQL)
-- Description: Removes "More from Mentor" fields from lounges (moved to mentors table)
-- Date: 2026-02-02

-- Remove mentor profile fields from lounges table
ALTER TABLE lounges
    DROP COLUMN IF EXISTS mentor_title,
    DROP COLUMN IF EXISTS philosophy,
    DROP COLUMN IF EXISTS hobbies,
    DROP COLUMN IF EXISTS social_instagram,
    DROP COLUMN IF EXISTS social_tiktok,
    DROP COLUMN IF EXISTS social_linkedin,
    DROP COLUMN IF EXISTS social_youtube,
    DROP COLUMN IF EXISTS book_title,
    DROP COLUMN IF EXISTS book_description,
    DROP COLUMN IF EXISTS podcast_rec_title,
    DROP COLUMN IF EXISTS podcast_name,
    DROP COLUMN IF EXISTS podcast_youtube,
    DROP COLUMN IF EXISTS podcast_spotify,
    DROP COLUMN IF EXISTS podcast_apple,
    DROP COLUMN IF EXISTS quick_prompts;
