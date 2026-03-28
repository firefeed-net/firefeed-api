--
-- FireFeed API — Seed Data
-- Initializes default sources and RSS feeds
-- Executed after 02-migrations.sql
--

-- Устанавливаем схему
SELECT pg_catalog.set_config('search_path', 'public', false);

-- ========== SEED: sources ==========
-- Insert default news sources if they don't exist
INSERT INTO public.sources (id, name, alias, description, site_url, logo, created_at, updated_at)
VALUES 
    (1, 'BBC News', 'bbc', 'British Broadcasting Corporation - World news coverage', 'https://www.bbc.com', NULL, NOW(), NOW()),
    (2, 'The New York Times', 'nyt', 'The New York Times - Breaking news, US and world news', 'https://www.nytimes.com', NULL, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Reset sequence to continue from the highest id
SELECT setval('public.sources_id_seq', COALESCE((SELECT MAX(id) FROM public.sources), 1));

-- ========== SEED: rss_feeds ==========
-- Insert default RSS feeds for each source
-- Note: ON CONFLICT (url) because rss_feeds has unique constraint on url column
INSERT INTO public.rss_feeds (id, source_id, url, name, category_id, language, is_active, created_at, updated_at, cooldown_minutes, max_news_per_hour)
VALUES 
    -- BBC News feeds
    (1, 1, 'https://feeds.bbci.co.uk/news/rss.xml', 'BBC News - World', NULL, 'en', true, NOW(), NOW(), 10, 10),
    (2, 1, 'https://feeds.bbci.co.uk/news/technology/rss.xml', 'BBC News - Technology', NULL, 'en', true, NOW(), NOW(), 10, 10),
    
    -- New York Times feeds
    (3, 2, 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml', 'NYT - Home Page', NULL, 'en', true, NOW(), NOW(), 10, 10),
    (4, 2, 'https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml', 'NYT - Technology', NULL, 'en', true, NOW(), NOW(), 10, 10)
ON CONFLICT (url) DO NOTHING;

-- Reset sequence to continue from the highest id
SELECT setval('public.rss_feeds_id_seq', COALESCE((SELECT MAX(id) FROM public.rss_feeds), 1));

-- ========== SEED: categories (optional) ==========
-- Insert default categories if needed
INSERT INTO public.categories (id, name, display_name, created_at, updated_at)
VALUES 
    (1, 'world', 'World News', NOW(), NOW()),
    (2, 'technology', 'Technology', NOW(), NOW()),
    (3, 'politics', 'Politics', NOW(), NOW()),
    (4, 'business', 'Business', NOW(), NOW()),
    (5, 'science', 'Science', NOW(), NOW()),
    (6, 'health', 'Health', NOW(), NOW()),
    (7, 'sports', 'Sports', NOW(), NOW()),
    (8, 'entertainment', 'Entertainment', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Reset sequence to continue from the highest id
SELECT setval('public.categories_id_seq', COALESCE((SELECT MAX(id) FROM public.categories), 1));

-- Log success
DO $$
BEGIN
    RAISE NOTICE '✅ Seed data initialized: 2 sources, 4 RSS feeds, 8 categories';
END
$$;
