------------------------------------------------
----          [Zar - Url Shortener]         ----
------------------------------------------------


------------------------------------------------
----             [EXTENSIONS]               ----
------------------------------------------------
CREATE EXTENSION IF NOT EXISTS citext;


------------------------------------------------
----              [FUNCTIONS]               ----
------------------------------------------------
CREATE OR REPLACE FUNCTION create_user_login_attempt()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_login_attempts (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;  -- segurança contra duplicações
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


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


------------------------------------------------
----                [ENUMS]                 ----
------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'email_type'
    ) THEN
        EXECUTE $dom$
        CREATE DOMAIN email_type AS citext
        CHECK (
            VALUE = normalize_email(VALUE)
        );
        $dom$;
    END IF;
END$$;


------------------------------------------------
----                 [URLS]                 ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_url TEXT NOT NULL,
    short_code VARCHAR(7) NOT NULL,
    clicks INTEGER DEFAULT 0,
    qr_code_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT urls_unique_short_code_cstr UNIQUE (short_code)
);

CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code);
CREATE INDEX IF NOT EXISTS idx_original_url ON urls(original_url);
CREATE INDEX IF NOT EXISTS idx_created_at ON urls(created_at DESC);


------------------------------------------------
----                 [USERS]                ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email email_type NOT NULL,
    p_hash BYTEA NOT NULL,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT users_unique_email_cstr UNIQUE (email)
);

------------------------------------------------
----         [USER SESSIONS TOKENS]         ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS user_session_tokens (
    refresh_token TEXT NOT NULL,
    user_id UUID NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    device_name TEXT NOT NULL,
    device_ip INET NOT NULL,
    user_agent TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT user_session_tokens_pkey PRIMARY KEY (refresh_token),
    CONSTRAINT user_session_tokens_unique_user_device UNIQUE (user_id, device_ip, user_agent)
);

CREATE INDEX IF NOT EXISTS idx_user_session_tokens_user ON user_session_tokens(user_id);


------------------------------------------------
----         [USER LOGIN ATTEMPTS]          ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS user_login_attempts (
    user_id UUID PRIMARY KEY NOT NULL,
    attempts INT NOT NULL DEFAULT 0,
    last_failed_login TIMESTAMPTZ,
    locked_until TIMESTAMPTZ,
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE
);


------------------------------------------------
----              [USERS URLS]              ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS user_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    url_id UUID NOT NULL,
    is_favorite BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (url_id) REFERENCES urls(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT user_urls_unique_url UNIQUE (user_id, url_id)
);

CREATE INDEX IF NOT EXISTS idx_user_urls_user ON user_urls(user_id);


------------------------------------------------
----              [USERS URLS]              ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS url_analytics (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    url_id UUID NOT NULL,
    clicked_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    ip_address INET,
    country_code CHAR(2),
    city TEXT,
    user_agent TEXT,
    referer TEXT,
    device_type VARCHAR(20), -- mobile, desktop, tablet, bot
    browser VARCHAR(50),
    os VARCHAR(50),
    FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE
) PARTITION BY RANGE (clicked_at);

CREATE TABLE IF NOT EXISTS url_analytics_2025_01 PARTITION OF url_analytics FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
CREATE TABLE IF NOT EXISTS url_analytics_2025_02 PARTITION OF url_analytics FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
CREATE TABLE IF NOT EXISTS url_analytics_2025_03 PARTITION OF url_analytics FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_01 PARTITION OF url_analytics FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_02 PARTITION OF url_analytics FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE IF NOT EXISTS url_analytics_2026_03 PARTITION OF url_analytics FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE INDEX IF NOT EXISTS idx_url_analytics_url ON url_analytics(url_id, clicked_at DESC);
CREATE INDEX IF NOT EXISTS idx_url_analytics_date ON url_analytics(clicked_at DESC);

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
    stacktrace TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);


------------------------------------------------
----           [RATE LIMIT LOGS]            ----
------------------------------------------------
CREATE TABLE IF NOT EXISTS rate_limit_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ip_address INET NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    attempts BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_attempt_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT rate_limit_logs_unique_cstr UNIQUE (ip_address, path, method)
);


------------------------------------------------
----              [TRIGGERS]                ----
------------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'trg_create_user_login_attempt'
    ) THEN
        CREATE TRIGGER trg_create_user_login_attempt
        AFTER INSERT ON users
        FOR EACH ROW
        EXECUTE FUNCTION create_user_login_attempt();
    END IF;
END;
$$;


------------------------------------------------
----                [VIEW]                  ----
------------------------------------------------

-- View: URLs mais populares
CREATE OR REPLACE VIEW v_popular_urls AS
SELECT 
    u.id::text,
    u.short_code,
    u.original_url,
    u.clicks,
    TO_CHAR(u.created_at, 'DD-MM-YYYY HH24:MI:SS') as created_at,
    COUNT(DISTINCT ua.id) as unique_clicks
FROM 
    urls u
LEFT JOIN 
    url_analytics ua ON u.id = ua.url_id
LEFT JOIN 
    user_urls uu ON u.id = uu.url_id
GROUP BY 
    u.id
ORDER BY 
    u.clicks DESC;


-- View: Estatísticas por usuário

CREATE OR REPLACE VIEW v_user_stats AS
SELECT 
    u.id::text,
    u.email,
    TO_CHAR(u.created_at, 'DD-MM-YYYY HH24:MI:SS') as member_since,
    COUNT(DISTINCT uu.url_id) as total_urls,
    COUNT(DISTINCT CASE WHEN uu.is_favorite THEN uu.url_id END) as favorite_urls,
    COALESCE(SUM(urls.clicks), 0) as total_clicks,
    TO_CHAR(MAX(urls.created_at), 'DD-MM-YYYY HH24:MI:SS') as last_url_created
FROM 
    users u
LEFT JOIN 
    user_urls uu ON u.id = uu.user_id
LEFT JOIN 
    urls ON uu.url_id = urls.id
GROUP BY 
    u.id;


-- View: Analytics agregados por dia
CREATE OR REPLACE VIEW v_daily_analytics AS
SELECT 
    url_id::text,
    TO_CHAR(DATE(clicked_at), 'DD-MM-YYYY') as date,
    COUNT(*) as clicks,
    COUNT(DISTINCT ip_address) as unique_visitors,
    COUNT(DISTINCT country_code) as countries,
    array_agg(DISTINCT device_type) FILTER (WHERE device_type IS NOT NULL) as device_types
FROM 
    url_analytics
GROUP BY 
    url_id, 
    DATE(clicked_at)
ORDER BY 
    date DESC;


-- View: Sessões ativas
CREATE OR REPLACE VIEW v_active_sessions AS
SELECT 
    ust.refresh_token,
    u.email,
    ust.device_name,
    ust.device_ip,
    ust.issued_at,
    ust.expires_at,
    EXTRACT(EPOCH FROM (ust.expires_at - NOW())) / 3600 as hours_until_expiry
FROM 
    user_session_tokens ust
JOIN 
    users u ON ust.user_id = u.id
WHERE 
    ust.expires_at > NOW() AND 
    ust.revoked = FALSE
ORDER BY 
    ust.issued_at DESC;


------------------------------------------------
----          [MATERIALIZED VIEW]           ----
------------------------------------------------

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM urls) as total_urls,
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT SUM(clicks) FROM urls) as total_clicks,
    (SELECT COUNT(*) FROM url_analytics WHERE clicked_at > NOW() - INTERVAL '24 hours') as clicks_last_24h,
    (SELECT COUNT(*) FROM urls WHERE created_at > NOW() - INTERVAL '7 days') as urls_created_last_week,
    TO_CHAR(NOW(), 'DD-MM-YYYY HH24:MI:SS') as last_updated;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dashboard_stats ON mv_dashboard_stats(last_updated);

-- Função para refresh automático
CREATE OR REPLACE FUNCTION refresh_dashboard_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_stats;
END;
$$ LANGUAGE plpgsql;