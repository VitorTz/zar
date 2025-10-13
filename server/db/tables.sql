------------------------------------------------
----          [Zar - Url Shortener]         ----
----              SCHEMA V2.0                ----
------------------------------------------------

------------------------------------------------
----                [DROPS]                 ----
------------------------------------------------

------------------------------------------------
----             [EXTENSIONS]               ----
------------------------------------------------
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

------------------------------------------------
----              [FUNCTIONS]               ----
------------------------------------------------

-- Função para criar registro de tentativas de login
CREATE OR REPLACE FUNCTION create_user_login_attempt()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_login_attempts (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Função para normalizar email
CREATE OR REPLACE FUNCTION normalize_email(input_email TEXT)
RETURNS TEXT AS $$
DECLARE
    cleaned TEXT;
BEGIN    
    cleaned := lower(trim(input_email));

    IF cleaned !~* '^[A-Za-z0-9._%+-]+@(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$' THEN
        RAISE EXCEPTION 'Invalid email format: %', input_email
            USING ERRCODE = '22000';
    END IF;

    RETURN cleaned;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- Função para incrementar clicks atomicamente (evita race conditions)
CREATE OR REPLACE FUNCTION increment_url_clicks(p_short_code TEXT)
RETURNS void AS $$
BEGIN
    UPDATE urls 
    SET clicks = clicks + 1,
        last_clicked_at = NOW()
    WHERE short_code = p_short_code;
END;
$$ LANGUAGE plpgsql;

-- Função para limpar sessões expiradas (manutenção)
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_session_tokens
    WHERE expires_at < NOW() - INTERVAL '7 days'
       OR (revoked = TRUE AND issued_at < NOW() - INTERVAL '30 days');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Função para limpar analytics antigos (manutenção)
CREATE OR REPLACE FUNCTION cleanup_old_analytics(months_to_keep INTEGER DEFAULT 12)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM url_analytics
    WHERE clicked_at < NOW() - (months_to_keep || ' months')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

------------------------------------------------
----                [DOMAINS]               ----
------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'email_type'
    ) THEN
        CREATE DOMAIN email_type AS citext
        CHECK (VALUE = normalize_email(VALUE));
    END IF;
END$$;

------------------------------------------------
----                 [USERS]                ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email email_type NOT NULL,
    p_hash BYTEA NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT users_unique_email_cstr UNIQUE (email)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

------------------------------------------------
----         [USER SESSIONS TOKENS]         ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS user_session_tokens (
    refresh_token TEXT PRIMARY KEY,
    user_id UUID NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,
    device_name TEXT NOT NULL,
    device_ip INET NOT NULL,
    user_agent TEXT NOT NULL,
    last_used_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_user_session_user FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT user_session_tokens_unique_user_device UNIQUE (user_id, device_ip, user_agent),
    CONSTRAINT chk_expires_after_issued CHECK (expires_at > issued_at),
    CONSTRAINT chk_revoked_at_when_revoked CHECK ((revoked = FALSE AND revoked_at IS NULL) OR (revoked = TRUE AND revoked_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_user_session_tokens_user ON user_session_tokens(user_id) WHERE revoked = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_session_tokens_expires ON user_session_tokens(expires_at) WHERE revoked = FALSE;

------------------------------------------------
----         [USER LOGIN ATTEMPTS]          ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS user_login_attempts (
    user_id UUID PRIMARY KEY,
    attempts INT NOT NULL DEFAULT 0,
    last_failed_login TIMESTAMPTZ,
    locked_until TIMESTAMPTZ,
    last_successful_login TIMESTAMPTZ,
    CONSTRAINT fk_login_attempts_user FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT chk_attempts_non_negative CHECK (attempts >= 0),
    CONSTRAINT chk_attempts_reasonable CHECK (attempts <= 1000)
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_locked ON user_login_attempts(locked_until) WHERE locked_until IS NOT NULL;

------------------------------------------------
----                 [URLS]                 ----
------------------------------------------------

CREATE TABLE IF NOT EXISTS urls (    
    short_code TEXT PRIMARY KEY,
    user_id UUID,
    p_hash BYTEA, -- Para URLs privadas/protegidas
    original_url TEXT NOT NULL,
    title TEXT, -- Título da página (útil para UX)
    clicks INTEGER DEFAULT 0 NOT NULL,
    last_clicked_at TIMESTAMPTZ,
    qrcode_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMPTZ,
    is_favorite BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    custom_alias BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT fk_urls_user FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT chk_short_code_format CHECK (short_code ~ '^[a-zA-Z0-9_-]{3,12}$'),
    CONSTRAINT chk_original_url CHECK (original_url ~ '^(https?://)([A-Za-z0-9-]+\.)+[A-Za-z]{2,}(/.*)?$'),
    CONSTRAINT chk_expires_after_created CHECK (expires_at IS NULL OR expires_at > created_at),
    CONSTRAINT chk_clicks_non_negative CHECK (clicks >= 0)
);

CREATE INDEX IF NOT EXISTS idx_urls_user_id ON urls(user_id, created_at DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_created_at ON urls(created_at DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_expires_at ON urls(expires_at) WHERE expires_at IS NOT NULL AND is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_clicks ON urls(clicks DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_original_url_hash ON urls USING hash(original_url);

------------------------------------------------
----                 [URLS]                 ----
------------------------------------------------

CREATE TABLE IF NOT EXISTS url_blacklist (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT url_blacklist_unique_cstr UNIQUE (url)
);

------------------------------------------------
----               [URL TAGS]               ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS url_tags (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id UUID NOT NULL,
    tag_color TEXT NOT NULL DEFAULT '#d8775a',
    tag_name citext NOT NULL,
    descr TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_url_tags_user FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT urls_tags_unique_tag UNIQUE (user_id, tag_name),
    CONSTRAINT chk_tag_color_hex CHECK (tag_color ~ '^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'),
    CONSTRAINT chk_tag_name_length CHECK (length(tag_name) BETWEEN 1 AND 64)
);

CREATE INDEX IF NOT EXISTS idx_url_tags_user ON url_tags(user_id);

-- Tabela de relacionamento muitos-para-muitos
CREATE TABLE IF NOT EXISTS url_tag_relations (
    url_short_code TEXT NOT NULL,
    tag_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (url_short_code, tag_id),
    CONSTRAINT fk_url_tag_rel_url FOREIGN KEY (url_short_code) REFERENCES urls(short_code) ON DELETE CASCADE,
    CONSTRAINT fk_url_tag_rel_tag FOREIGN KEY (tag_id) REFERENCES url_tags(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_url_tag_relations_tag ON url_tag_relations(tag_id);

------------------------------------------------
----             [URL ANALYTICS]            ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS url_analytics (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    short_code TEXT NOT NULL,
    clicked_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    ip_address INET,
    country_code CHAR(2),
    city TEXT,
    user_agent TEXT,
    referer TEXT,
    device_type VARCHAR(20), -- mobile, desktop, tablet, bot
    browser VARCHAR(50),
    os VARCHAR(50),
    PRIMARY KEY (id, clicked_at),
    CONSTRAINT fk_analytics_url FOREIGN KEY (short_code) REFERENCES urls(short_code) ON DELETE CASCADE
) PARTITION BY RANGE (clicked_at);

-- Criar partições para os próximos 12 meses
CREATE TABLE IF NOT EXISTS url_analytics_2025_10 PARTITION OF url_analytics FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
CREATE TABLE IF NOT EXISTS url_analytics_2025_11 PARTITION OF url_analytics FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE IF NOT EXISTS url_analytics_2025_12 PARTITION OF url_analytics FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_01 PARTITION OF url_analytics FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_02 PARTITION OF url_analytics FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_03 PARTITION OF url_analytics FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_04 PARTITION OF url_analytics FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_05 PARTITION OF url_analytics FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_06 PARTITION OF url_analytics FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_07 PARTITION OF url_analytics FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_08 PARTITION OF url_analytics FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_09 PARTITION OF url_analytics FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

CREATE INDEX IF NOT EXISTS idx_url_analytics_short_code ON url_analytics(short_code, clicked_at DESC);
CREATE INDEX IF NOT EXISTS idx_url_analytics_date ON url_analytics(clicked_at DESC);
CREATE INDEX IF NOT EXISTS idx_url_analytics_country ON url_analytics(country_code) WHERE country_code IS NOT NULL;

------------------------------------------------
----                 [LOGS]                 ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    level VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    path TEXT,
    method VARCHAR(10),
    status_code INT,
    user_id UUID,
    stacktrace TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT chk_log_level CHECK (level IN ('DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'))
);

CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id) WHERE user_id IS NOT NULL;

------------------------------------------------
----           [RATE LIMIT LOGS]            ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS rate_limit_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ip_address INET NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    attempts BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_attempt_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    window_start TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT rate_limit_logs_unique_cstr UNIQUE (ip_address, path, method, window_start)
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_ip ON rate_limit_logs(ip_address, last_attempt_at DESC);
CREATE INDEX IF NOT EXISTS idx_rate_limit_cleanup ON rate_limit_logs(last_attempt_at);

------------------------------------------------
----              [TRIGGERS]                ----
------------------------------------------------

-- Trigger para criar registro de login attempts
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trg_create_user_login_attempt'
    ) THEN
        CREATE TRIGGER trg_create_user_login_attempt
        AFTER INSERT ON users
        FOR EACH ROW
        EXECUTE FUNCTION create_user_login_attempt();
    END IF;
END$$;

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trg_users_updated_at'
    ) THEN
        CREATE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trg_urls_updated_at'
    ) THEN
        CREATE TRIGGER trg_urls_updated_at
        BEFORE UPDATE ON urls
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END$$;

------------------------------------------------
----                [VIEWS]                 ----
------------------------------------------------

-- View de URLs populares
CREATE OR REPLACE VIEW v_popular_urls AS
SELECT
    MIN(u.short_code) AS short_code, -- apenas um exemplo de short_code
    u.original_url,
    MIN(u.title) AS title,
    SUM(u.clicks) AS clicks,
    MIN(u.created_at) AS created_at,
    MAX(u.last_clicked_at) AS last_clicked_at,
    COUNT(DISTINCT ua.id) AS unique_visitors,
    COUNT(DISTINCT ua.country_code) AS countries_reached
FROM 
    urls u
LEFT JOIN 
    url_analytics ua ON u.short_code = ua.short_code
WHERE 
    u.is_active = TRUE
GROUP BY 
    u.original_url
ORDER BY 
    SUM(u.clicks) DESC;


-- View de estatísticas de usuário
CREATE OR REPLACE VIEW v_user_stats AS
SELECT 
    u.id,
    u.email,
    u.created_at as member_since,
    COUNT(DISTINCT urls.short_code) as total_urls,
    COUNT(DISTINCT urls.short_code) FILTER (WHERE urls.is_favorite) as favorite_urls,
    COALESCE(SUM(urls.clicks), 0) as total_clicks,
    MAX(urls.created_at) as last_url_created,
    MAX(urls.last_clicked_at) as last_click_received
FROM 
    users u
LEFT JOIN 
    urls ON urls.user_id = u.id AND urls.is_active = TRUE
WHERE 
    u.is_active = TRUE
GROUP BY 
    u.id, 
    u.email, 
    u.created_at;

-- View de sessões ativas
CREATE OR REPLACE VIEW v_active_sessions AS
SELECT 
    ust.refresh_token,
    u.email,
    ust.device_name,
    ust.device_ip,
    ust.issued_at,
    ust.last_used_at,
    ust.expires_at,
    EXTRACT(EPOCH FROM (ust.expires_at - NOW())) / 3600 as hours_until_expiry
FROM user_session_tokens ust
JOIN users u ON ust.user_id = u.id
WHERE ust.expires_at > NOW() 
  AND ust.revoked = FALSE
  AND u.is_active = TRUE
ORDER BY ust.last_used_at DESC;

-- View de analytics diários (otimizada)
CREATE OR REPLACE VIEW v_daily_analytics AS
SELECT 
    short_code,
    DATE(clicked_at) as date,
    COUNT(*) as total_clicks,
    COUNT(DISTINCT ip_address) as unique_visitors,
    COUNT(DISTINCT country_code) as countries,
    ARRAY_AGG(DISTINCT device_type) FILTER (WHERE device_type IS NOT NULL) as device_types,
    ARRAY_AGG(DISTINCT browser) FILTER (WHERE browser IS NOT NULL) as browsers
FROM url_analytics
GROUP BY short_code, DATE(clicked_at)
ORDER BY date DESC;


-- View de estatísticas de URL (últimos 30 dias)
CREATE OR REPLACE VIEW vw_url_stats AS
WITH recent_analytics AS (
    SELECT *
    FROM url_analytics
    WHERE clicked_at >= NOW() - INTERVAL '30 days'
)
SELECT
    u.short_code,
    COALESCE(COUNT(ra.id), 0) AS total_clicks,
    COALESCE(COUNT(DISTINCT ra.ip_address), 0) AS unique_visitors,
    MIN(ra.clicked_at) AS first_click,
    MAX(ra.clicked_at) AS last_click,

    COALESCE((
        SELECT JSONB_AGG(jsonb_build_object('day', day, 'clicks', clicks) ORDER BY day DESC)
        FROM (
            SELECT 
                DATE(clicked_at) AS day,
                COUNT(*) AS clicks
            FROM recent_analytics ra2
            WHERE ra2.short_code = u.short_code
            GROUP BY DATE(clicked_at)
        ) t
    ), '[]'::jsonb) AS timeline,

    COALESCE((
        SELECT JSONB_AGG(jsonb_build_object('country_code', country_code, 'clicks', clicks) ORDER BY clicks DESC)
        FROM (
            SELECT country_code, COUNT(*) as clicks
            FROM recent_analytics ra2
            WHERE ra2.short_code = u.short_code 
              AND country_code IS NOT NULL
            GROUP BY country_code
            LIMIT 10
        ) t
    ), '[]'::jsonb) AS top_countries,

    COALESCE((
        SELECT JSONB_AGG(jsonb_build_object('city', city, 'clicks', clicks) ORDER BY clicks DESC)
        FROM (
            SELECT city, COUNT(*) as clicks
            FROM recent_analytics ra3
            WHERE ra3.short_code = u.short_code 
              AND city IS NOT NULL
            GROUP BY city
            LIMIT 5
        ) t
    ), '[]'::jsonb) AS top_cities,

    COALESCE((
        SELECT JSONB_OBJECT_AGG(device_type, count)
        FROM (
            SELECT device_type, COUNT(*) as count
            FROM recent_analytics ra4
            WHERE ra4.short_code = u.short_code 
              AND device_type IS NOT NULL
            GROUP BY device_type
        ) x
    ), '{}'::jsonb) AS devices,

    COALESCE((
        SELECT JSONB_OBJECT_AGG(browser, count)
        FROM (
            SELECT browser, COUNT(*) as count
            FROM recent_analytics ra5
            WHERE ra5.short_code = u.short_code 
              AND browser IS NOT NULL
            GROUP BY browser
        ) x
    ), '{}'::jsonb) AS browsers,

    COALESCE((
        SELECT JSONB_OBJECT_AGG(os, count)
        FROM (
            SELECT os, COUNT(*) as count
            FROM recent_analytics ra6
            WHERE ra6.short_code = u.short_code 
              AND os IS NOT NULL
            GROUP BY os
        ) x
    ), '{}'::jsonb) AS operating_systems,

    COALESCE((
        SELECT JSONB_AGG(jsonb_build_object('referer', referer, 'clicks', clicks) ORDER BY clicks DESC)
        FROM (
            SELECT referer, COUNT(*) as clicks
            FROM recent_analytics ra7
            WHERE ra7.short_code = u.short_code 
              AND referer IS NOT NULL 
              AND referer != ''
            GROUP BY referer
            LIMIT 5
        ) t
    ), '[]'::jsonb) AS top_referers

FROM urls u
LEFT JOIN recent_analytics ra ON ra.short_code = u.short_code
GROUP BY u.short_code;

------------------------------------------------
----          [MATERIALIZED VIEWS]          ----
------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_stats AS
WITH 
-- Estatísticas gerais de URLs
url_stats AS (
    SELECT 
        COUNT(*) as total_urls,
        COUNT(*) FILTER (WHERE is_favorite = TRUE) as favorite_urls,
        COUNT(*) FILTER (WHERE custom_alias = TRUE) as custom_alias_urls,
        COUNT(*) FILTER (WHERE p_hash IS NOT NULL) as protected_urls,
        COUNT(*) FILTER (WHERE expires_at IS NOT NULL AND expires_at > NOW()) as expiring_urls,
        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as urls_created_last_24h,
        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as urls_created_last_7d,
        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as urls_created_last_30d,
        COALESCE(SUM(clicks), 0) as total_clicks,
        COALESCE(AVG(clicks), 0) as avg_clicks_per_url,
        COALESCE(MAX(clicks), 0) as max_clicks_single_url
    FROM urls 
    WHERE is_active = TRUE
),
-- Estatísticas de usuários
user_stats AS (
    SELECT 
        COUNT(*) as total_users,
        COUNT(*) FILTER (WHERE is_verified = TRUE) as verified_users,
        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as new_users_last_7d,
        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as new_users_last_30d,
        COUNT(*) FILTER (WHERE last_login_at > NOW() - INTERVAL '24 hours') as users_active_last_24h,
        COUNT(*) FILTER (WHERE last_login_at > NOW() - INTERVAL '7 days') as users_active_last_7d
    FROM users 
    WHERE is_active = TRUE
),
-- Estatísticas de analytics/clicks
analytics_stats AS (
    SELECT 
        COUNT(*) FILTER (WHERE clicked_at > NOW() - INTERVAL '1 hour') as clicks_last_hour,
        COUNT(*) FILTER (WHERE clicked_at > NOW() - INTERVAL '24 hours') as clicks_last_24h,
        COUNT(*) FILTER (WHERE clicked_at > NOW() - INTERVAL '7 days') as clicks_last_7d,
        COUNT(*) FILTER (WHERE clicked_at > NOW() - INTERVAL '30 days') as clicks_last_30d,
        COUNT(DISTINCT ip_address) FILTER (WHERE clicked_at > NOW() - INTERVAL '24 hours') as unique_visitors_24h,
        COUNT(DISTINCT ip_address) FILTER (WHERE clicked_at > NOW() - INTERVAL '7 days') as unique_visitors_7d,
        COUNT(DISTINCT country_code) FILTER (WHERE clicked_at > NOW() - INTERVAL '30 days') as countries_reached_30d
    FROM url_analytics
),
-- Top URLs por clicks
top_urls AS (
    SELECT JSONB_AGG(
        jsonb_build_object(
            'short_code', short_code,
            'original_url', LEFT(original_url, 50) || CASE WHEN LENGTH(original_url) > 50 THEN '...' ELSE '' END,
            'clicks', total_clicks            
        ) ORDER BY total_clicks DESC
    ) AS top_10_urls
    FROM (
        SELECT 
            original_url,
            SUM(clicks) AS total_clicks,
            (ARRAY_AGG(short_code ORDER BY clicks DESC))[1] AS short_code
        FROM 
            urls
        WHERE 
            is_active = TRUE
        GROUP BY 
            original_url
        ORDER BY 
            total_clicks DESC
        LIMIT 10
    ) t
),
-- Distribuição de dispositivos (últimos 7 dias)
device_distribution AS (
    SELECT JSONB_OBJECT_AGG(
        COALESCE(device_type, 'unknown'), 
        count
    ) as device_stats
    FROM (
        SELECT 
            device_type,
            COUNT(*) as count
        FROM url_analytics
        WHERE clicked_at > NOW() - INTERVAL '7 days'
          AND device_type IS NOT NULL
        GROUP BY device_type
    ) d
),
-- Top países (últimos 30 dias)
top_countries AS (
    SELECT JSONB_AGG(
        jsonb_build_object(
            'country_code', country_code,
            'clicks', clicks
        ) ORDER BY clicks DESC
    ) as top_10_countries
    FROM (
        SELECT 
            country_code,
            COUNT(*) as clicks
        FROM url_analytics
        WHERE clicked_at > NOW() - INTERVAL '30 days'
          AND country_code IS NOT NULL
        GROUP BY country_code
        ORDER BY clicks DESC
        LIMIT 10
    ) c
),
-- Sessões ativas
session_stats AS (
    SELECT 
        COUNT(*) as active_sessions,
        COUNT(DISTINCT user_id) as users_with_active_sessions,
        COUNT(*) FILTER (WHERE last_used_at > NOW() - INTERVAL '1 hour') as sessions_active_last_hour
    FROM user_session_tokens
    WHERE expires_at > NOW() 
      AND revoked = FALSE
),
-- Tags mais utilizadas
tag_stats AS (
    WITH tag_usage AS (
        SELECT tag_id, COUNT(*) AS usage_count
        FROM url_tag_relations
        GROUP BY tag_id
    )
    SELECT 
        (SELECT COUNT(*) FROM tag_usage) AS total_tags,
        (
            SELECT JSONB_AGG(
                jsonb_build_object(
                    'tag_name', ut.tag_name,
                    'usage_count', tu.usage_count,
                    'tag_color', ut.tag_color
                ) ORDER BY tu.usage_count DESC
            )
            FROM (
                SELECT tu.tag_id, tu.usage_count
                FROM tag_usage tu
                ORDER BY tu.usage_count DESC
                LIMIT 10
            ) tu
            JOIN url_tags ut ON ut.id = tu.tag_id
        ) AS top_10_tags
),
-- Timeline de crescimento (últimos 30 dias)
growth_timeline AS (
    SELECT JSONB_AGG(
        jsonb_build_object(
            'date', date,
            'new_urls', new_urls,
            'new_users', new_users,
            'total_clicks', total_clicks
        ) ORDER BY date DESC
    ) as last_30_days_timeline
    FROM (
        SELECT 
            date_series::DATE as date,
            (SELECT COUNT(*) FROM urls WHERE DATE(created_at) = date_series::DATE AND is_active = TRUE) as new_urls,
            (SELECT COUNT(*) FROM users WHERE DATE(created_at) = date_series::DATE AND is_active = TRUE) as new_users,
            (SELECT COUNT(*) FROM url_analytics WHERE DATE(clicked_at) = date_series::DATE) as total_clicks
        FROM generate_series(
            NOW() - INTERVAL '29 days',
            NOW(),
            INTERVAL '1 day'
        ) as date_series
    ) t
)
SELECT 
    -- URLs
    us.total_urls,
    us.favorite_urls,
    us.custom_alias_urls,
    us.protected_urls,
    us.expiring_urls,
    us.urls_created_last_24h,
    us.urls_created_last_7d,
    us.urls_created_last_30d,
    us.total_clicks,
    ROUND(us.avg_clicks_per_url::NUMERIC, 2) as avg_clicks_per_url,
    us.max_clicks_single_url,
    
    -- Usuários
    u.total_users,
    u.verified_users,
    u.new_users_last_7d,
    u.new_users_last_30d,
    u.users_active_last_24h,
    u.users_active_last_7d,
    
    -- Analytics/Clicks
    a.clicks_last_hour,
    a.clicks_last_24h,
    a.clicks_last_7d,
    a.clicks_last_30d,
    a.unique_visitors_24h,
    a.unique_visitors_7d,
    a.countries_reached_30d,
    
    -- Sessões
    ss.active_sessions,
    ss.users_with_active_sessions,
    ss.sessions_active_last_hour,
    
    -- Tags
    COALESCE(ts.total_tags, 0) as total_tags,
    COALESCE(ts.top_10_tags, '[]'::jsonb) as top_tags,
    
    -- Agregados complexos
    COALESCE(tu.top_10_urls, '[]'::jsonb) as top_urls,
    COALESCE(dd.device_stats, '{}'::jsonb) as device_distribution,
    COALESCE(tc.top_10_countries, '[]'::jsonb) as top_countries,
    COALESCE(gt.last_30_days_timeline, '[]'::jsonb) as growth_timeline,
    
    -- Metadados
    NOW() as last_updated,
    TO_CHAR(NOW(), 'DD-MM-YYYY HH24:MI:SS') as last_updated_formatted
FROM 
    url_stats us,
    user_stats u,
    analytics_stats a,
    session_stats ss,
    top_urls tu,
    device_distribution dd,
    top_countries tc,
    tag_stats ts,
    growth_timeline gt;

-- Índice único para refresh concorrente
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dashboard_stats_updated ON mv_dashboard_stats(last_updated);


------------------------------------------------
----        [FUNÇÃO DE REFRESH]             ----
------------------------------------------------
CREATE OR REPLACE FUNCTION refresh_dashboard_stats()
RETURNS TABLE(
    execution_time_ms NUMERIC,
    refreshed_at TIMESTAMPTZ
) AS $$
DECLARE
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
    last_refresh TIMESTAMPTZ;
BEGIN
    start_time := clock_timestamp();
    
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_stats;
    
    end_time := clock_timestamp();

    SELECT 
        m.last_updated
    INTO 
        last_refresh
    FROM 
        mv_dashboard_stats AS m
    LIMIT 1;

    RETURN QUERY
    SELECT 
        ROUND(EXTRACT(EPOCH FROM (end_time - start_time)) * 1000, 2) AS execution_time_ms,
        last_refresh AS refreshed_at;
END;
$$ LANGUAGE plpgsql;

------------------------------------------------
----          [REFRESH SCHEDULES]           ----
------------------------------------------------
-- Execute via cron ou pg_cron:
-- SELECT cron.schedule('refresh-dashboard', '*/5 * * * *', 'SELECT refresh_dashboard_stats()');
-- SELECT cron.schedule('cleanup-sessions', '0 3 * * *', 'SELECT cleanup_expired_sessions()');
-- SELECT cron.schedule('cleanup-analytics', '0 4 1 * *', 'SELECT cleanup_old_analytics(12)');
