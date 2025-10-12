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

-- Função para refresh do dashboard
CREATE OR REPLACE FUNCTION refresh_dashboard_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_stats;
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
    CONSTRAINT chk_original_url_format CHECK (original_url ~ '^https?://'),
    CONSTRAINT chk_expires_after_created CHECK (expires_at IS NULL OR expires_at > created_at),
    CONSTRAINT chk_clicks_non_negative CHECK (clicks >= 0)
);

CREATE INDEX IF NOT EXISTS idx_urls_user_id ON urls(user_id, created_at DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_created_at ON urls(created_at DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_expires_at ON urls(expires_at) WHERE expires_at IS NOT NULL AND is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_clicks ON urls(clicks DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_urls_original_url_hash ON urls USING hash(original_url);

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
    u.short_code,
    u.original_url,
    u.title,
    u.clicks,
    u.created_at,
    u.last_clicked_at,
    COUNT(DISTINCT ua.id) as unique_visitors,
    COUNT(DISTINCT ua.country_code) as countries_reached
FROM 
    urls u
LEFT JOIN 
    url_analytics ua ON u.short_code = ua.short_code
WHERE 
    u.is_active = TRUE
GROUP BY 
    u.short_code, 
    u.original_url, 
    u.title, 
    u.clicks, 
    u.created_at, 
    u.last_clicked_at
ORDER BY 
    u.clicks DESC;

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
FROM users u
LEFT JOIN urls ON urls.user_id = u.id AND urls.is_active = TRUE
WHERE u.is_active = TRUE
GROUP BY u.id, u.email, u.created_at;

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
    ra.short_code,
    COUNT(*) AS total_clicks,
    COUNT(DISTINCT ip_address) AS unique_visitors,
    MIN(clicked_at) AS first_click,
    MAX(clicked_at) AS last_click,
    
    -- Timeline diário
    (
        SELECT JSONB_AGG(jsonb_build_object('day', day, 'clicks', clicks) ORDER BY day DESC)
        FROM (
            SELECT 
                DATE(clicked_at) AS day,
                COUNT(*) AS clicks
            FROM recent_analytics ra2
            WHERE ra2.short_code = ra.short_code
            GROUP BY DATE(clicked_at)
        ) t
    ) AS timeline,
    
    -- Top países
    (
        SELECT JSONB_AGG(jsonb_build_object('country_code', country_code, 'clicks', clicks) ORDER BY clicks DESC)
        FROM (
            SELECT country_code, COUNT(*) as clicks
            FROM recent_analytics ra2
            WHERE ra2.short_code = ra.short_code 
              AND country_code IS NOT NULL
            GROUP BY country_code
            LIMIT 10
        ) t
    ) AS top_countries,
    
    -- Top cidades
    (
        SELECT JSONB_AGG(jsonb_build_object('city', city, 'clicks', clicks) ORDER BY clicks DESC)
        FROM (
            SELECT city, COUNT(*) as clicks
            FROM recent_analytics ra3
            WHERE ra3.short_code = ra.short_code 
              AND city IS NOT NULL
            GROUP BY city
            LIMIT 5
        ) t
    ) AS top_cities,
    
    -- Distribuição de dispositivos
    (
        SELECT JSONB_OBJECT_AGG(device_type, count)
        FROM (
            SELECT device_type, COUNT(*) as count
            FROM recent_analytics ra4
            WHERE ra4.short_code = ra.short_code 
              AND device_type IS NOT NULL
            GROUP BY device_type
        ) x
    ) AS devices,
    
    -- Navegadores
    (
        SELECT JSONB_OBJECT_AGG(browser, count)
        FROM (
            SELECT browser, COUNT(*) as count
            FROM recent_analytics ra5
            WHERE ra5.short_code = ra.short_code 
              AND browser IS NOT NULL
            GROUP BY browser
        ) x
    ) AS browsers,
    
    -- Sistemas operacionais
    (
        SELECT JSONB_OBJECT_AGG(os, count)
        FROM (
            SELECT os, COUNT(*) as count
            FROM recent_analytics ra6
            WHERE ra6.short_code = ra.short_code 
              AND os IS NOT NULL
            GROUP BY os
        ) x
    ) AS operating_systems,
    
    -- Top referers
    (
        SELECT JSONB_AGG(jsonb_build_object('referer', referer, 'clicks', clicks) ORDER BY clicks DESC)
        FROM (
            SELECT referer, COUNT(*) as clicks
            FROM recent_analytics ra7
            WHERE ra7.short_code = ra.short_code 
              AND referer IS NOT NULL 
              AND referer != ''
            GROUP BY referer
            LIMIT 5
        ) t
    ) AS top_referers

FROM recent_analytics ra
GROUP BY ra.short_code;

------------------------------------------------
----          [MATERIALIZED VIEWS]          ----
------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM urls WHERE is_active = TRUE) as total_urls,
    (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as total_users,
    (SELECT COALESCE(SUM(clicks), 0) FROM urls WHERE is_active = TRUE) as total_clicks,
    (SELECT COUNT(*) FROM url_analytics WHERE clicked_at > NOW() - INTERVAL '24 hours') as clicks_last_24h,
    (SELECT COUNT(*) FROM url_analytics WHERE clicked_at > NOW() - INTERVAL '7 days') as clicks_last_7d,
    (SELECT COUNT(*) FROM urls WHERE created_at > NOW() - INTERVAL '7 days' AND is_active = TRUE) as urls_created_last_week,
    (SELECT COUNT(DISTINCT user_id) FROM user_session_tokens WHERE last_used_at > NOW() - INTERVAL '24 hours' AND revoked = FALSE) as active_users_24h,
    NOW() as last_updated;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dashboard_stats ON mv_dashboard_stats(last_updated);

------------------------------------------------
----          [REFRESH SCHEDULES]           ----
------------------------------------------------
-- Execute via cron ou pg_cron:
-- SELECT cron.schedule('refresh-dashboard', '*/5 * * * *', 'SELECT refresh_dashboard_stats()');
-- SELECT cron.schedule('cleanup-sessions', '0 3 * * *', 'SELECT cleanup_expired_sessions()');
-- SELECT cron.schedule('cleanup-analytics', '0 4 1 * *', 'SELECT cleanup_old_analytics(12)');
