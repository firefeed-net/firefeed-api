--
-- FireFeed API — Clean Database Schema
-- Owner: firefeed_api
-- Auto-generated: safe for initialization via docker-entrypoint-initdb.d
--

-- Устанавливаем схему
SELECT pg_catalog.set_config('search_path', 'public', false);

-- Расширения (на всякий случай — уже могут быть созданы)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- ========== TABLE: categories ==========
CREATE TABLE IF NOT EXISTS public.categories (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    display_name character varying(100),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS public.categories_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;
ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq');

ALTER TABLE public.categories ADD CONSTRAINT idx_16802_primary PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_16802_unique_name ON public.categories USING btree (name);

-- ========== TABLE: sources ==========
CREATE TABLE IF NOT EXISTS public.sources (
    id bigint NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone,
    alias character varying(255),
    logo character varying(500),
    site_url character varying(255)
);

CREATE SEQUENCE IF NOT EXISTS public.sources_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.sources_id_seq OWNED BY public.sources.id;
ALTER TABLE ONLY public.sources ALTER COLUMN id SET DEFAULT nextval('public.sources_id_seq');

ALTER TABLE public.sources ADD CONSTRAINT idx_16842_primary PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_16842_unique_name ON public.sources USING btree (name);

-- ========== TABLE: rss_feeds ==========
CREATE TABLE IF NOT EXISTS public.rss_feeds (
    id bigint NOT NULL,
    source_id bigint NOT NULL,
    url character varying(500) NOT NULL,
    name character varying(255) NOT NULL,
    category_id bigint,
    language character varying(10) NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone,
    cooldown_minutes integer DEFAULT 10,
    max_news_per_hour integer DEFAULT 10
);

CREATE SEQUENCE IF NOT EXISTS public.rss_feeds_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.rss_feeds_id_seq OWNED BY public.rss_feeds.id;
ALTER TABLE ONLY public.rss_feeds ALTER COLUMN id SET DEFAULT nextval('public.rss_feeds_id_seq');

ALTER TABLE public.rss_feeds ADD CONSTRAINT idx_16833_primary PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_16833_unique_feed ON public.rss_feeds USING btree (url);
CREATE INDEX IF NOT EXISTS idx_rss_feeds_category_id ON public.rss_feeds USING btree (category_id);
CREATE INDEX IF NOT EXISTS idx_rss_feeds_source_id ON public.rss_feeds USING btree (source_id);
CREATE INDEX IF NOT EXISTS idx_rss_feeds_is_active ON public.rss_feeds USING btree (is_active);

-- ========== TABLE: rss_data ==========
CREATE TABLE IF NOT EXISTS public.rss_data (
    news_id character varying(255) NOT NULL,
    original_title text NOT NULL,
    original_content text NOT NULL,
    original_language character varying(10) NOT NULL,
    category_id bigint,
    image_filename character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone,
    rss_feed_id bigint,
    embedding public.vector(384),
    source_url text,
    video_filename text
);

ALTER TABLE public.rss_data ADD CONSTRAINT idx_16825_primary PRIMARY KEY (news_id);
CREATE INDEX IF NOT EXISTS idx_rss_data_category_id ON public.rss_data USING btree (category_id);
CREATE INDEX IF NOT EXISTS idx_rss_data_created_at_desc ON public.rss_data USING btree (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rss_data_rss_feed_id ON public.rss_data USING btree (rss_feed_id);
CREATE INDEX IF NOT EXISTS idx_rss_data_original_title_trgm ON public.rss_data USING gin (original_title public.gin_trgm_ops) WHERE (original_title IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_rss_data_original_content_trgm ON public.rss_data USING gin (original_content public.gin_trgm_ops) WHERE (original_content IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_rss_data_embedding ON public.rss_data USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');

-- ========== TABLE: news_translations ==========
CREATE TABLE IF NOT EXISTS public.news_translations (
    id bigint NOT NULL,
    news_id character varying(255) NOT NULL,
    language character varying(10) NOT NULL,
    translated_title text NOT NULL,
    translated_content text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS public.news_translations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.news_translations_id_seq OWNED BY public.news_translations.id;
ALTER TABLE ONLY public.news_translations ALTER COLUMN id SET DEFAULT nextval('public.news_translations_id_seq');

ALTER TABLE public.news_translations ADD CONSTRAINT idx_16809_primary PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_16809_unique_news_lang ON public.news_translations USING btree (news_id, language);
CREATE INDEX IF NOT EXISTS idx_16809_idx_news_id ON public.news_translations USING btree (news_id);
CREATE INDEX IF NOT EXISTS idx_16809_idx_language ON public.news_translations USING btree (language);
CREATE INDEX IF NOT EXISTS idx_news_translations_translated_title_trgm ON public.news_translations USING gin (translated_title public.gin_trgm_ops) WHERE (translated_title IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_news_translations_translated_content_trgm ON public.news_translations USING gin (translated_content public.gin_trgm_ops) WHERE (translated_content IS NOT NULL);

-- ========== TABLE: users ==========
CREATE TABLE IF NOT EXISTS public.users (
    id bigint NOT NULL,
    email character varying(255) NOT NULL,
    password_hash text NOT NULL,
    language character varying(2) DEFAULT 'en'::character varying,
    is_active boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_verified boolean DEFAULT false NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL
);

CREATE SEQUENCE IF NOT EXISTS public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;
ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq');

ALTER TABLE public.users ADD CONSTRAINT users_pkey PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON public.users USING btree (email);
CREATE INDEX IF NOT EXISTS idx_users_is_verified ON public.users USING btree (is_verified);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON public.users USING btree (is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_deleted ON public.users USING btree (is_deleted);

-- ========== TABLE: user_preferences ==========
CREATE TABLE IF NOT EXISTS public.user_preferences (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    subscriptions text,
    language character varying(2) DEFAULT 'en'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.user_preferences_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_preferences_id_seq OWNED BY public.user_preferences.id;
ALTER TABLE ONLY public.user_preferences ALTER COLUMN id SET DEFAULT nextval('public.user_preferences_id_seq');

ALTER TABLE public.user_preferences ADD CONSTRAINT user_preferences_pkey PRIMARY KEY (id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON public.user_preferences USING btree (user_id);

-- ========== TABLE: user_rss_feeds ==========
CREATE TABLE IF NOT EXISTS public.user_rss_feeds (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    url character varying(500) NOT NULL,
    name character varying(255),
    category_id bigint,
    language character varying(10) DEFAULT 'en'::character varying,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.user_rss_feeds_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_rss_feeds_id_seq OWNED BY public.user_rss_feeds.id;
ALTER TABLE ONLY public.user_rss_feeds ALTER COLUMN id SET DEFAULT nextval('public.user_rss_feeds_id_seq');

ALTER TABLE public.user_rss_feeds ADD CONSTRAINT user_rss_feeds_pkey PRIMARY KEY (id);
CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_user_id ON public.user_rss_feeds USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_category_id ON public.user_rss_feeds USING btree (category_id);
CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_is_active ON public.user_rss_feeds USING btree (is_active);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_rss_feeds_user_url ON public.user_rss_feeds USING btree (user_id, url);

-- ========== TABLE: user_api_keys ==========
CREATE TABLE IF NOT EXISTS public.user_api_keys (
    id integer NOT NULL,
    user_id integer NOT NULL,
    key_hash text NOT NULL,
    limits jsonb DEFAULT '{"requests_per_day": 1000, "requests_per_hour": 100}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS public.user_api_keys_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_api_keys_id_seq OWNED BY public.user_api_keys.id;
ALTER TABLE ONLY public.user_api_keys ALTER COLUMN id SET DEFAULT nextval('public.user_api_keys_id_seq');

ALTER TABLE public.user_api_keys ADD CONSTRAINT user_api_keys_pkey PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS user_api_keys_key_hash_key ON public.user_api_keys USING btree (key_hash);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON public.user_api_keys USING btree (user_id);

-- ========== TABLE: password_reset_tokens ==========
CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    token text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS public.password_reset_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.password_reset_tokens_id_seq OWNED BY public.password_reset_tokens.id;
ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN id SET DEFAULT nextval('public.password_reset_tokens_id_seq');

ALTER TABLE public.password_reset_tokens ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON public.password_reset_tokens USING btree (token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON public.password_reset_tokens USING btree (user_id);

-- ========== TABLE: user_verification_codes ==========
CREATE TABLE IF NOT EXISTS public.user_verification_codes (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    verification_code character varying(6) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone
);

CREATE SEQUENCE IF NOT EXISTS public.user_verification_codes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_verification_codes_id_seq OWNED BY public.user_verification_codes.id;
ALTER TABLE ONLY public.user_verification_codes ALTER COLUMN id SET DEFAULT nextval('public.user_verification_codes_id_seq');

ALTER TABLE public.user_verification_codes ADD CONSTRAINT user_verification_codes_pkey PRIMARY KEY (id);
CREATE INDEX IF NOT EXISTS idx_user_verification_codes_user_id ON public.user_verification_codes USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_user_verification_codes_code ON public.user_verification_codes USING btree (verification_code);
CREATE INDEX IF NOT EXISTS idx_user_verification_codes_expires_at ON public.user_verification_codes USING btree (expires_at);

-- ========== TABLE: user_telegram_links ==========
CREATE TABLE IF NOT EXISTS public.user_telegram_links (
    id integer NOT NULL,
    user_id integer NOT NULL,
    telegram_id bigint,
    link_code character varying(32),
    created_at timestamp with time zone DEFAULT now(),
    linked_at timestamp with time zone,
    CONSTRAINT telegram_link_check CHECK ((((telegram_id IS NULL) AND (linked_at IS NULL)) OR ((telegram_id IS NOT NULL) AND (linked_at IS NOT NULL))))
);

CREATE SEQUENCE IF NOT EXISTS public.user_telegram_links_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_telegram_links_id_seq OWNED BY public.user_telegram_links.id;
ALTER TABLE ONLY public.user_telegram_links ALTER COLUMN id SET DEFAULT nextval('public.user_telegram_links_id_seq');

ALTER TABLE public.user_telegram_links ADD CONSTRAINT user_telegram_links_pkey PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS user_telegram_links_telegram_id_key ON public.user_telegram_links USING btree (telegram_id);
CREATE UNIQUE INDEX IF NOT EXISTS user_telegram_links_link_code_key ON public.user_telegram_links USING btree (link_code);
CREATE INDEX IF NOT EXISTS idx_user_telegram_links_user_id ON public.user_telegram_links USING btree (user_id);

-- ========== TABLE: rss_items_telegram_bot_published ==========
CREATE TABLE IF NOT EXISTS public.rss_items_telegram_bot_published (
    id integer NOT NULL,
    news_id character varying(255),
    translation_id integer,
    recipient_type character varying(10) NOT NULL,
    recipient_id bigint NOT NULL,
    message_id bigint,
    language character varying(5),
    sent_at timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT rss_items_telegram_bot_published_recipient_type_check CHECK (((recipient_type)::text = ANY ((ARRAY['channel'::character varying, 'user'::character varying])::text[])))
);

CREATE SEQUENCE IF NOT EXISTS public.rss_items_telegram_bot_published_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.rss_items_telegram_bot_published_id_seq OWNED BY public.rss_items_telegram_bot_published.id;
ALTER TABLE ONLY public.rss_items_telegram_bot_published ALTER COLUMN id SET DEFAULT nextval('public.rss_items_telegram_bot_published_id_seq');

ALTER TABLE public.rss_items_telegram_bot_published ADD CONSTRAINT rss_items_telegram_bot_published_pkey PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS rss_items_telegram_bot_publis_news_id_translation_id_recipi_key ON public.rss_items_telegram_bot_published USING btree (news_id, translation_id, recipient_type, recipient_id);

-- ========== TABLE: source_categories ==========
CREATE TABLE IF NOT EXISTS public.source_categories (
    source_id bigint NOT NULL,
    category_id bigint NOT NULL
);

ALTER TABLE public.source_categories ADD CONSTRAINT source_categories_pkey PRIMARY KEY (source_id, category_id);
CREATE INDEX IF NOT EXISTS idx_source_categories_source_id_category_id ON public.source_categories USING btree (source_id, category_id);

-- ========== TABLE: user_categories ==========
CREATE TABLE IF NOT EXISTS public.user_categories (
    user_id bigint NOT NULL,
    category_id integer NOT NULL
);

ALTER TABLE public.user_categories ADD CONSTRAINT user_categories_pkey PRIMARY KEY (user_id, category_id);
CREATE INDEX IF NOT EXISTS idx_user_categories_user_id ON public.user_categories USING btree (user_id);
CREATE INDEX IF NOT EXISTS idx_user_categories_category_id ON public.user_categories USING btree (category_id);

-- ========== FK Constraints ==========
ALTER TABLE ONLY public.rss_feeds ADD CONSTRAINT fk_feeds_category_id FOREIGN KEY (category_id) REFERENCES public.categories(id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE ONLY public.rss_data ADD CONSTRAINT fk_rss_data_category_id FOREIGN KEY (category_id) REFERENCES public.categories(id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE ONLY public.rss_data ADD CONSTRAINT fk_rss_data_rss_feed_id FOREIGN KEY (rss_feed_id) REFERENCES public.rss_feeds(id) ON UPDATE CASCADE ON DELETE SET NULL;
ALTER TABLE ONLY public.news_translations ADD CONSTRAINT fk_translations_news_id FOREIGN KEY (news_id) REFERENCES public.rss_data(news_id) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE ONLY public.source_categories ADD CONSTRAINT source_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.source_categories ADD CONSTRAINT source_categories_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.sources(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.user_preferences ADD CONSTRAINT user_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.user_rss_feeds ADD CONSTRAINT user_rss_feeds_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.user_rss_feeds ADD CONSTRAINT user_rss_feeds_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.user_categories ADD CONSTRAINT user_categories_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.user_categories ADD CONSTRAINT user_categories_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.password_reset_tokens ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.user_verification_codes ADD CONSTRAINT user_verification_codes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.user_api_keys ADD CONSTRAINT user_api_keys_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.user_telegram_links ADD CONSTRAINT user_telegram_links_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

-- ========== Set ownership to firefeed_api ==========
ALTER TABLE public.categories OWNER TO firefeed_api;
ALTER TABLE public.sources OWNER TO firefeed_api;
ALTER TABLE public.rss_feeds OWNER TO firefeed_api;
ALTER TABLE public.rss_data OWNER TO firefeed_api;
ALTER TABLE public.news_translations OWNER TO firefeed_api;
ALTER TABLE public.users OWNER TO firefeed_api;
ALTER TABLE public.user_preferences OWNER TO firefeed_api;
ALTER TABLE public.user_rss_feeds OWNER TO firefeed_api;
ALTER TABLE public.user_api_keys OWNER TO firefeed_api;
ALTER TABLE public.password_reset_tokens OWNER TO firefeed_api;
ALTER TABLE public.user_verification_codes OWNER TO firefeed_api;
ALTER TABLE public.user_telegram_links OWNER TO firefeed_api;
ALTER TABLE public.rss_items_telegram_bot_published OWNER TO firefeed_api;
ALTER TABLE public.source_categories OWNER TO firefeed_api;
ALTER TABLE public.user_categories OWNER TO firefeed_api;
