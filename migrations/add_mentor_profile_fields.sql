-- Migration: Add mentor profile fields to lounges table
-- Description: Adds fields for "More from Mentor" modal content
-- Date: 2026-02-02

-- Mentor profile fields for "More from Mentor" modal
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS mentor_title VARCHAR(255) NULL;
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS philosophy TEXT NULL;
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS hobbies TEXT NULL;

-- Social links
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS social_instagram VARCHAR(500) NULL;
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS social_tiktok VARCHAR(500) NULL;
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS social_linkedin VARCHAR(500) NULL;
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS social_youtube VARCHAR(500) NULL;

-- Book recommendation
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS book_title VARCHAR(500) NULL;
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS book_description TEXT NULL;

-- Podcast recommendation
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS podcast_rec_title VARCHAR(500) NULL;

-- Podcast links (More from me section)
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS podcast_name VARCHAR(255) NULL;
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS podcast_youtube VARCHAR(500) NULL;
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS podcast_spotify VARCHAR(500) NULL;
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS podcast_apple VARCHAR(500) NULL;

-- Quick prompts - JSON array of prompt strings
ALTER TABLE lounges ADD COLUMN IF NOT EXISTS quick_prompts TEXT NULL;

-- Add comments for documentation
COMMENT ON COLUMN lounges.mentor_title IS 'Mentor title displayed in modal (e.g., Mindset mentor)';
COMMENT ON COLUMN lounges.philosophy IS 'Mentor philosophy/bio text';
COMMENT ON COLUMN lounges.hobbies IS 'JSON array of hobbies/interests';
COMMENT ON COLUMN lounges.social_instagram IS 'Instagram profile URL';
COMMENT ON COLUMN lounges.social_tiktok IS 'TikTok profile URL';
COMMENT ON COLUMN lounges.social_linkedin IS 'LinkedIn profile URL';
COMMENT ON COLUMN lounges.social_youtube IS 'YouTube channel URL';
COMMENT ON COLUMN lounges.book_title IS 'Recommended book title';
COMMENT ON COLUMN lounges.book_description IS 'Book recommendation description';
COMMENT ON COLUMN lounges.podcast_rec_title IS 'Recommended podcast title';
COMMENT ON COLUMN lounges.podcast_name IS 'Mentor own podcast name';
COMMENT ON COLUMN lounges.podcast_youtube IS 'Podcast YouTube URL';
COMMENT ON COLUMN lounges.podcast_spotify IS 'Podcast Spotify URL';
COMMENT ON COLUMN lounges.podcast_apple IS 'Podcast Apple Podcasts URL';
COMMENT ON COLUMN lounges.quick_prompts IS 'JSON array of quick prompt strings';
